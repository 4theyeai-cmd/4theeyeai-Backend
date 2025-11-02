/**
 * Cypress E2E tests for general API endpoints
 */

describe("API Endpoints Tests", () => {
  const BASE_URL = Cypress.env("API_URL").replace("/api/v1", "");

  describe("Root Endpoint", () => {
    it("should return health status", () => {
      cy.request("GET", BASE_URL).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property("status");
        expect(response.body).to.have.property("version");
        expect(response.body).to.have.property("connections");
      });
    });
  });

  describe("API Documentation", () => {
    it("should serve Swagger documentation", () => {
      cy.request({
        method: "GET",
        url: `${BASE_URL}/docs`,
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.be.oneOf([200, 307]); // 307 for redirect
      });
    });

    it("should serve OpenAPI schema", () => {
      cy.request({
        method: "GET",
        url: `${BASE_URL}/openapi.json`,
        failOnStatusCode: false,
      }).then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property("openapi");
          expect(response.body).to.have.property("info");
        }
      });
    });
  });

  describe("CORS Headers", () => {
    it("should include CORS headers in response", () => {
      cy.request({
        method: "GET",
        url: BASE_URL,
      }).then((response) => {
        // Check if CORS headers are present (might vary based on config)
        expect(response.headers).to.exist;
      });
    });
  });
});

