// Stub for jsPDF's optional canvg import.
// We use html2canvas to rasterize the DOM before passing to jsPDF,
// so canvg (SVG→Canvas) is never actually invoked.
export default {};
