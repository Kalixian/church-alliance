function PageBanner({ eyebrow, title, children }) {
  return (
    <section className="page-banner">
      {eyebrow ? <p className="page-banner__eyebrow">{eyebrow}</p> : null}
      <h1>{title}</h1>
      {children ? <p>{children}</p> : null}
    </section>
  )
}

export default PageBanner
