var physiomeportal = require("physiomeportal");

var main = function()  {
  var moduleManager = undefined;
  var UIIsReady = true;
  var managerSidebar = undefined;
  var _this = this;

  /**
   * Initialise all the panels required for PJP to function correctly.
   * Modules used incude - {@link PJP.ModelsLoader}, {@link PJP.BodyViewer},
   * {@link PJP.OrgansViewer}, {@link PJP.TissueViewer}, {@link PJP.CellPanel}
   * and {@link PJP.ModelPanel}.
   */
  var initialiseMain = function() {
      var scaffoldViewer = new physiomeportal.ScaffoldViewer();
      var scaffoldDialog = new physiomeportal.ScaffoldDialog(scaffoldViewer);
      scaffoldViewer.setName("ScaffoldMaker");
      scaffoldDialog.setLeft("0");
      scaffoldDialog.setWidth("100%");
      scaffoldDialog.setHeight("100%");
      scaffoldDialog.destroyModuleOnClose = true;
  }

  var initialise = function() {
    initialiseMain();
  }


  initialise();
}

window.document.addEventListener('DOMContentLoaded', main);