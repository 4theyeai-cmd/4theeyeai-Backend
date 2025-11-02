// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

/**
 * Custom command to upload a PDF file
 * @param {string} companyName - Name of the company
 * @param {string} filePath - Path to the PDF file
 * @param {string} description - Optional description
 */
Cypress.Commands.add("uploadPDF", (companyName, filePath, description = null) => {
  cy.fixture(filePath, "base64").then((fileContent) => {
    cy.get('input[type="file"]').selectFile(
      {
        contents: Cypress.Buffer.from(fileContent, "base64"),
        fileName: filePath.split("/").pop(),
        mimeType: "application/pdf",
      },
      { force: true }
    );

    cy.get('input[name="company_name"]').type(companyName);

    if (description) {
      cy.get('input[name="description"]').type(description);
    }

    cy.get('button[type="submit"]').click();
  });
});

/**
 * Custom command to wait for API response
 */
Cypress.Commands.add("waitForAPI", (alias) => {
  cy.wait(alias).then((interception) => {
    expect(interception.response.statusCode).to.be.oneOf([200, 201]);
  });
});

/**
 * Custom command to check API health
 */
Cypress.Commands.add("checkAPIHealth", () => {
  cy.request("GET", Cypress.env("API_URL").replace("/api/v1", "")).then(
    (response) => {
      expect(response.status).to.eq(200);
      expect(response.body.status).to.eq("running");
    }
  );
});

