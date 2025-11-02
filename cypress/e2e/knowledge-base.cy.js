/**
 * Cypress E2E tests for Knowledge Base API
 */

describe("Knowledge Base API Tests", () => {
  const API_URL = Cypress.env("API_URL");
  const BASE_URL = Cypress.env("API_URL").replace("/api/v1", "");
  const TEST_COMPANY = "CypressTestCompany";

  before(() => {
    // Check if API is running
    cy.request({
      method: "GET",
      url: BASE_URL,
      failOnStatusCode: false,
    }).then((response) => {
      if (response.status !== 200) {
        throw new Error("API server is not running. Please start the server first.");
      }
    });
  });

  beforeEach(() => {
    // Clean up test data before each test
    cy.request({
      method: "DELETE",
      url: `${API_URL}/knowledge-base/company/${TEST_COMPANY}`,
      failOnStatusCode: false,
    });
  });

  after(() => {
    // Clean up test data after all tests
    cy.request({
      method: "DELETE",
      url: `${API_URL}/knowledge-base/company/${TEST_COMPANY}`,
      failOnStatusCode: false,
    });
  });

  describe("API Health Check", () => {
    it("should check API health status", () => {
      cy.request("GET", BASE_URL).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property("status");
        expect(response.body.status).to.eq("running");
      });
    });
  });

  describe("PDF Upload", () => {
    it("should upload a PDF file successfully", () => {
      // Create a minimal PDF content for testing
      const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
xref
0 2
trailer
<<
/Size 2
/Root 1 0 R
>>
%%EOF`;

      const blob = new Blob([pdfContent], { type: "application/pdf" });
      const file = new File([blob], "test.pdf", { type: "application/pdf" });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("company_name", TEST_COMPANY);
      formData.append("description", "Test PDF upload from Cypress");

      cy.request({
        method: "POST",
        url: `${API_URL}/knowledge-base/upload`,
        body: formData,
        headers: {
          // Don't set Content-Type, let the browser set it with boundary
        },
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property("company_name", TEST_COMPANY);
        expect(response.body).to.have.property("file_name", "test.pdf");
        expect(response.body).to.have.property("id");
      });
    });

    it("should reject non-PDF files", () => {
      const blob = new Blob(["This is not a PDF"], { type: "text/plain" });
      const file = new File([blob], "test.txt", { type: "text/plain" });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("company_name", TEST_COMPANY);

      cy.request({
        method: "POST",
        url: `${API_URL}/knowledge-base/upload`,
        body: formData,
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.be.oneOf([400, 422]);
      });
    });

    it("should require company_name", () => {
      const pdfContent = `%PDF-1.4
%%EOF`;
      const blob = new Blob([pdfContent], { type: "application/pdf" });
      const file = new File([blob], "test.pdf", { type: "application/pdf" });

      const formData = new FormData();
      formData.append("file", file);
      // Missing company_name

      cy.request({
        method: "POST",
        url: `${API_URL}/knowledge-base/upload`,
        body: formData,
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(422);
      });
    });
  });

  describe("Question Answering", () => {
    let documentId;

    before(() => {
      // Upload a PDF first
      const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
xref
0 2
trailer
<<
/Size 2
/Root 1 0 R
>>
%%EOF`;

      const blob = new Blob([pdfContent], { type: "application/pdf" });
      const file = new File([blob], "test.pdf", { type: "application/pdf" });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("company_name", TEST_COMPANY);

      cy.request({
        method: "POST",
        url: `${API_URL}/knowledge-base/upload`,
        body: formData,
      }).then((response) => {
        documentId = response.body.id;
        // Wait for vector store to be created
        cy.wait(2000);
      });
    });

    it("should return 404 when asking question without knowledge base", () => {
      cy.request({
        method: "POST",
        url: `${API_URL}/knowledge-base/question`,
        body: {
          company_name: "NonExistentCompany",
          question: "What is your policy?",
        },
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(404);
        expect(response.body.detail).to.include("No knowledge base found");
      });
    });

    it("should require company_name and question", () => {
      // Missing fields
      cy.request({
        method: "POST",
        url: `${API_URL}/knowledge-base/question`,
        body: {},
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(422);
      });
    });
  });

  describe("Document Management", () => {
    let documentId;

    beforeEach(() => {
      // Upload a PDF for testing
      const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
xref
0 2
trailer
<<
/Size 2
/Root 1 0 R
>>
%%EOF`;

      const blob = new Blob([pdfContent], { type: "application/pdf" });
      const file = new File([blob], "test.pdf", { type: "application/pdf" });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("company_name", TEST_COMPANY);

      cy.request({
        method: "POST",
        url: `${API_URL}/knowledge-base/upload`,
        body: formData,
      }).then((response) => {
        documentId = response.body.id;
      });
    });

    it("should get all documents for a company", () => {
      cy.request({
        method: "GET",
        url: `${API_URL}/knowledge-base/documents/${TEST_COMPANY}`,
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.be.an("array");
        expect(response.body.length).to.be.greaterThan(0);
      });
    });

    it("should get a specific document by ID", () => {
      cy.request({
        method: "GET",
        url: `${API_URL}/knowledge-base/document/${documentId}`,
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property("id", documentId);
        expect(response.body).to.have.property("company_name", TEST_COMPANY);
      });
    });

    it("should return 404 for non-existent document", () => {
      cy.request({
        method: "GET",
        url: `${API_URL}/knowledge-base/document/99999`,
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(404);
      });
    });

    it("should delete a document", () => {
      cy.request({
        method: "DELETE",
        url: `${API_URL}/knowledge-base/document/${documentId}`,
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body.message).to.include("deleted successfully");
      });

      // Verify document is deleted
      cy.request({
        method: "GET",
        url: `${API_URL}/knowledge-base/document/${documentId}`,
        failOnStatusCode: false,
      }).then((response) => {
        expect(response.status).to.eq(404);
      });
    });

    it("should delete all documents for a company", () => {
      cy.request({
        method: "DELETE",
        url: `${API_URL}/knowledge-base/company/${TEST_COMPANY}`,
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body.message).to.include("deleted");
      });

      // Verify documents are deleted
      cy.request({
        method: "GET",
        url: `${API_URL}/knowledge-base/documents/${TEST_COMPANY}`,
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.be.an("array");
        expect(response.body.length).to.eq(0);
      });
    });
  });
});

