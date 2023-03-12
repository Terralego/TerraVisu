/* globals cy */

/**
 * Layer id of the first layer from test data.
 * The id is created from md5 of the db id and the layer source slug
 * https://github.com/Terralego/terra-layer/blob/master/terra_layer/models.py#L190
 */
const testLayerId = '5b0371ebc5d25ba6f7ce7068a8a959a7';

describe('Map controls', () => {
  beforeEach(() => {
    cy.visit('/view/test_map_scene#map=7.85/44.064/5.974');
    cy.get('.splash-screen_container').should('be.visible');

    cy.get('.mapboxgl-ctrl-zoom-in', { timeout: 15000 });

    cy.get('.tf-map')
      .then($elt => Promise.resolve($elt[0].mapboxInstance))
      .as('mapinstance');

    cy.get('@mapinstance', { timeout: 15000 }).should(mapElt => {
      // Wait for tiles to be loaded
      expect(mapElt.areTilesLoaded()).to.be.true;
      // Wait for layer to exists in mapbox layers
      expect(
        mapElt
          .getStyle()
          .layers.find(({ id }) => id === testLayerId),
      ).to.exist;
      // Wait for tiles to be loaded
      expect(mapElt.areTilesLoaded()).to.be.true;
    }, { timeout: 10000 });

    // Wait for slapsh screen to close
    cy.get('.splash-screen_container', { timeout: 10000 }).should('not.be.visible');
  });

  it('Should zoom in and out', () => {
    // Get previous zoom
    cy.get('@mapinstance')
      .then(mapInstance => Promise.resolve(mapInstance.getZoom()))
      .as('prevZoom');

    // Click on button
    cy.get('.mapboxgl-ctrl-zoom-in').should('be.visible', { timeout: 5000 }).click();

    // Compare to new zoom
    cy.get('@mapinstance').then(mapInstance => {
      cy.get('@prevZoom').should(prevZoom => {
        expect(mapInstance.getZoom() > prevZoom).to.be.true;
      });
    });

    // Get previous zoom
    cy.get('@mapinstance')
      .then(mapboxInstance => Promise.resolve(mapboxInstance.getZoom()))
      .as('prevZoom');

    // Click on zoom out
    cy.get('.mapboxgl-ctrl-zoom-out').should('be.visible', { timeout: 5000 }).click();

    cy.get('@mapinstance').then(mapboxInstance => {
      cy.get('@prevZoom').should(prevZoom => {
        expect(mapboxInstance.getZoom() < prevZoom).to.be.true;
      });
    });
  });
});
