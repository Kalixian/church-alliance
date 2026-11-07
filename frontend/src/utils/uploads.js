// Picture uploads: the browser posts each file straight to Cloudinary using fields signed by our API,
// then sends Cloudinary's signed response to POST /api/v1/pictures to save it.

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024
const UPLOAD_CONCURRENCY = 3

// Uploads one file to Cloudinary; resolves with Cloudinary's signed response.
export const uploadToCloudinary = (uploadUrl, fields, file, onProgress) => new Promise((resolve, reject) => {
  const formData = new FormData()
  Object.entries(fields).forEach(([key, value]) => formData.append(key, value))
  formData.append('file', file)

  const request = new XMLHttpRequest()
  request.open('POST', uploadUrl)
  request.upload.onprogress = (event) => {
    if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100))
  }
  request.onload = () => {
    let body = {}
    try {
      body = JSON.parse(request.responseText)
    } catch {
      // Fall through to the generic error below.
    }
    if (request.status >= 200 && request.status < 300) {
      resolve(body)
    } else {
      reject(new Error(body.error?.message || 'Unable to upload photo.'))
    }
  }
  request.onerror = () => reject(new Error('Unable to reach the photo service. Please try again.'))
  request.send(formData)
})

const responseError = async (response, fallback) => {
  const body = await response.json().catch(() => ({}))
  return new Error(body.detail || fallback)
}

// Returns an error message if the file can't be uploaded, otherwise null.
export const validateImageFile = (file) => {
  if (!file.type.startsWith('image/')) return `${file.name} is not an image.`
  if (file.size > MAX_UPLOAD_BYTES) return `${file.name} is larger than 10 MB.`
  return null
}

export const fetchUploadSignature = async (apiBaseUrl, token) => {
  const response = await fetch(`${apiBaseUrl}/api/v1/pictures/upload-signature`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw await responseError(response, 'Unable to upload photo.')
  return response.json()
}

export const confirmPicture = async (apiBaseUrl, token, uploaded, { caption, galleryId }) => {
  const response = await fetch(`${apiBaseUrl}/api/v1/pictures`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      public_id: uploaded.public_id,
      version: uploaded.version,
      signature: uploaded.signature,
      caption: caption?.trim() || null,
      gallery_id: galleryId,
    }),
  })
  if (!response.ok) throw await responseError(response, 'Unable to save photo.')
  return response.json()
}

// Uploads many files into one gallery, a few at a time, sharing one signature (valid for an hour).
// `items` are { key, file, caption }; `onItemChange(key, changes)` reports progress and per-file results.
// Resolves once every file has finished, whether or not it succeeded.
export const uploadPictures = async ({ apiBaseUrl, token, galleryId, items, onItemChange }) => {
  const { upload_url: uploadUrl, fields } = await fetchUploadSignature(apiBaseUrl, token)
  const queue = [...items]

  const worker = async () => {
    while (queue.length > 0) {
      const item = queue.shift()
      onItemChange(item.key, { status: 'uploading', progress: 0, error: '' })
      try {
        const uploaded = await uploadToCloudinary(uploadUrl, fields, item.file, (progress) => {
          onItemChange(item.key, { progress })
        })
        const picture = await confirmPicture(apiBaseUrl, token, uploaded, { caption: item.caption, galleryId })
        onItemChange(item.key, { status: 'done', progress: 100, picture })
      } catch (error) {
        onItemChange(item.key, { status: 'error', error: error.message || 'Unable to upload photo.' })
      }
    }
  }

  await Promise.all(Array.from({ length: Math.min(UPLOAD_CONCURRENCY, items.length) }, worker))
}

let nextQueueKey = 0

export const fetchGalleryPictures = async (apiBaseUrl, galleryId) => {
  const response = await fetch(`${apiBaseUrl}/api/v1/galleries/${galleryId}/pictures`)
  if (!response.ok) throw new Error('Unable to load photos.')
  return response.json()
}

// Builds queue entries for picked files, plus messages for any that were rejected.
export const queueFiles = (files) => {
  const queued = []
  const rejected = []
  for (const file of files) {
    const problem = validateImageFile(file)
    if (problem) {
      rejected.push(problem)
    } else {
      nextQueueKey += 1
      queued.push({
        key: `queued-${nextQueueKey}`,
        file,
        previewUrl: URL.createObjectURL(file),
        caption: '',
        status: 'queued',
        progress: 0,
        error: '',
      })
    }
  }
  return { queued, rejected }
}
