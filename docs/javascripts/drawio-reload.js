document$.subscribe(({ body }) => {
  // if drawio toolbar icons/buttons are not showing or missing due to title being longer than the image width
  // you can set a minimum width for the graph viewer by uncommenting the following line
  // GraphViewer.prototype.minWidth = 500;

  GraphViewer.processElements()

  // required to fix duplicate display of external drawio graphs (via http)
  reload();
})