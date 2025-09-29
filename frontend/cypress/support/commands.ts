/// <reference types="cypress" />

// Custom commands for TradingAgents application

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to login with username and password
       * @example cy.login('testuser', 'password123')
       */
      login(username: string, password: string): Chainable<void>;
      
      /**
       * Custom command to logout
       * @example cy.logout()
       */
      logout(): Chainable<void>;
      
      /**
       * Custom command to wait for API response
       * @example cy.waitForApi('@getAnalysis')
       */
      waitForApi(alias: string): Chainable<void>;
      
      /**
       * Custom command to mock API responses
       * @example cy.mockApiResponse('POST', '/api/auth/login', { fixture: 'user.json' })
       */
      mockApiResponse(method: string, url: string, response: any): Chainable<void>;
      
      /**
       * Custom command to check loading state
       * @example cy.checkLoadingState()
       */
      checkLoadingState(): Chainable<void>;
    }
  }
}

// Login command
Cypress.Commands.add('login', (username: string, password: string) => {
  cy.visit('/login');
  cy.get('[placeholder="用户名"]').type(username);
  cy.get('[placeholder="密码"]').type(password);
  cy.get('button[type="submit"]').click();
  
  // Wait for login to complete
  cy.url().should('not.include', '/login');
});

// Logout command
Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="user-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/login');
});

// Wait for API command
Cypress.Commands.add('waitForApi', (alias: string) => {
  cy.wait(alias).then((interception) => {
    expect(interception.response?.statusCode).to.be.oneOf([200, 201, 204]);
  });
});

// Mock API response command
Cypress.Commands.add('mockApiResponse', (method: string, url: string, response: any) => {
  cy.intercept(method, url, response).as(url.replace(/[^a-zA-Z0-9]/g, ''));
});

// Check loading state command
Cypress.Commands.add('checkLoadingState', () => {
  cy.get('.ant-spin').should('be.visible');
  cy.get('.ant-spin').should('not.exist');
});

export {};