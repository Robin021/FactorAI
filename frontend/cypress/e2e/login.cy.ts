describe('Login Flow E2E Tests', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    cy.clearLocalStorage();
    
    // Mock API responses
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          permissions: ['read'],
        },
        token: 'mock-jwt-token',
      },
    }).as('loginRequest');
    
    cy.intercept('GET', '/api/auth/me', {
      statusCode: 200,
      body: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'user',
        permissions: ['read'],
      },
    }).as('getCurrentUser');
  });

  it('should display login form correctly', () => {
    cy.visit('/login');
    
    // Check page elements
    cy.contains('因子智投').should('be.visible');
    cy.contains('因子驱动的智能投研平台').should('be.visible');
    cy.get('[placeholder="用户名"]').should('be.visible');
    cy.get('[placeholder="密码"]').should('be.visible');
    cy.get('button[type="submit"]').should('contain', '登录');
    cy.get('input[type="checkbox"]').should('be.visible');
    cy.contains('记住用户名').should('be.visible');
  });

  it('should validate form fields', () => {
    cy.visit('/login');
    
    // Try to submit empty form
    cy.get('button[type="submit"]').click();
    
    // Check validation messages
    cy.contains('请输入用户名').should('be.visible');
    cy.contains('请输入密码').should('be.visible');
    
    // Test username validation
    cy.get('[placeholder="用户名"]').type('ab');
    cy.get('[placeholder="密码"]').type('password123');
    cy.get('button[type="submit"]').click();
    cy.contains('用户名至少3个字符').should('be.visible');
    
    // Test password validation
    cy.get('[placeholder="用户名"]').clear().type('testuser');
    cy.get('[placeholder="密码"]').clear().type('123');
    cy.get('button[type="submit"]').click();
    cy.contains('密码至少6个字符').should('be.visible');
  });

  it('should login successfully with valid credentials', () => {
    cy.visit('/login');
    
    // Fill in credentials
    cy.get('[placeholder="用户名"]').type('testuser');
    cy.get('[placeholder="密码"]').type('password123');
    
    // Submit form
    cy.get('button[type="submit"]').click();
    
    // Wait for API call
    cy.wait('@loginRequest');
    
    // Should redirect to dashboard
    cy.url().should('not.include', '/login');
    cy.url().should('include', '/dashboard');
    
    // Check success message
    cy.contains('登录成功').should('be.visible');
  });

  it('should handle login failure', () => {
    // Mock failed login
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 401,
      body: { message: '用户名或密码错误' },
    }).as('failedLogin');
    
    cy.visit('/login');
    
    // Fill in invalid credentials
    cy.get('[placeholder="用户名"]').type('wronguser');
    cy.get('[placeholder="密码"]').type('wrongpassword');
    cy.get('button[type="submit"]').click();
    
    // Wait for API call
    cy.wait('@failedLogin');
    
    // Should show error message
    cy.contains('登录失败').should('be.visible');
    cy.contains('用户名或密码错误').should('be.visible');
    
    // Should stay on login page
    cy.url().should('include', '/login');
  });

  it('should handle remember me functionality', () => {
    cy.visit('/login');
    
    // Fill in credentials and check remember me
    cy.get('[placeholder="用户名"]').type('testuser');
    cy.get('[placeholder="密码"]').type('password123');
    cy.get('input[type="checkbox"]').check();
    
    // Submit form
    cy.get('button[type="submit"]').click();
    cy.wait('@loginRequest');
    
    // Check localStorage
    cy.window().then((win) => {
      expect(win.localStorage.getItem('remember_me')).to.equal('true');
      expect(win.localStorage.getItem('saved_credentials')).to.contain('testuser');
    });
  });

  it('should load saved credentials on page load', () => {
    // Set saved credentials
    cy.window().then((win) => {
      win.localStorage.setItem('remember_me', 'true');
      win.localStorage.setItem('saved_credentials', JSON.stringify({ username: 'saveduser' }));
    });
    
    cy.visit('/login');
    
    // Check if credentials are loaded
    cy.get('[placeholder="用户名"]').should('have.value', 'saveduser');
    cy.get('input[type="checkbox"]').should('be.checked');
  });

  it('should handle multiple failed attempts with lockout', () => {
    // Mock failed login
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 401,
      body: { message: 'Invalid credentials' },
    }).as('failedLogin');
    
    cy.visit('/login');
    
    // Attempt login 5 times
    for (let i = 0; i < 5; i++) {
      cy.get('[placeholder="用户名"]').clear().type('wronguser');
      cy.get('[placeholder="密码"]').clear().type('wrongpassword');
      cy.get('button[type="submit"]').click();
      cy.wait('@failedLogin');
      
      // Check warning messages for attempts 3-4
      if (i >= 2 && i < 4) {
        cy.contains(`还有 ${4 - i} 次尝试机会`).should('be.visible');
      }
    }
    
    // After 5 attempts, should be locked out
    cy.contains('账户已锁定').should('be.visible');
    cy.get('button[type="submit"]').should('be.disabled');
  });

  it('should show loading state during login', () => {
    // Add delay to login request
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        user: { id: '1', username: 'testuser' },
        token: 'mock-token',
      },
      delay: 1000,
    }).as('slowLogin');
    
    cy.visit('/login');
    
    cy.get('[placeholder="用户名"]').type('testuser');
    cy.get('[placeholder="密码"]').type('password123');
    cy.get('button[type="submit"]').click();
    
    // Check loading state
    cy.get('button[type="submit"]').should('be.disabled');
    cy.get('.ant-spin').should('be.visible');
    
    cy.wait('@slowLogin');
    
    // Loading should disappear
    cy.get('.ant-spin').should('not.exist');
  });

  it('should handle network errors gracefully', () => {
    // Mock network error
    cy.intercept('POST', '/api/auth/login', {
      forceNetworkError: true,
    }).as('networkError');
    
    cy.visit('/login');
    
    cy.get('[placeholder="用户名"]').type('testuser');
    cy.get('[placeholder="密码"]').type('password123');
    cy.get('button[type="submit"]').click();
    
    cy.wait('@networkError');
    
    // Should show error message
    cy.contains('登录失败').should('be.visible');
  });

  it('should clear error when user dismisses alert', () => {
    // Mock failed login
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 401,
      body: { message: 'Login failed' },
    }).as('failedLogin');
    
    cy.visit('/login');
    
    cy.get('[placeholder="用户名"]').type('wronguser');
    cy.get('[placeholder="密码"]').type('wrongpassword');
    cy.get('button[type="submit"]').click();
    
    cy.wait('@failedLogin');
    
    // Error should be visible
    cy.contains('登录失败').should('be.visible');
    
    // Click close button
    cy.get('.ant-alert-close-icon').click();
    
    // Error should be hidden
    cy.contains('登录失败').should('not.exist');
  });
});
