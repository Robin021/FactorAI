describe('Analysis Workflow E2E Tests', () => {
  beforeEach(() => {
    // Clear localStorage and login
    cy.clearLocalStorage();
    
    // Mock authentication
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          permissions: ['read', 'write'],
        },
        token: 'mock-jwt-token',
      },
    }).as('login');
    
    cy.intercept('GET', '/api/auth/me', {
      statusCode: 200,
      body: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'user',
        permissions: ['read', 'write'],
      },
    }).as('getCurrentUser');
    
    // Mock analysis API endpoints
    cy.intercept('POST', '/api/analysis/start', {
      statusCode: 200,
      body: {
        id: 'analysis-123',
        user_id: '1',
        stock_code: '000001',
        market_type: 'CN',
        status: 'pending',
        progress: 0,
        config: {
          stock_code: '000001',
          market_type: 'CN',
          analysis_date: '2024-01-01',
          analysts: ['fundamentals', 'technical'],
          llm_config: { model: 'gpt-4' },
        },
        result_data: null,
        created_at: new Date().toISOString(),
        started_at: null,
        completed_at: null,
        error_message: null,
      },
    }).as('startAnalysis');
    
    cy.intercept('GET', '/api/analysis/*/status', {
      statusCode: 200,
      body: {
        id: 'analysis-123',
        status: 'running',
        progress: 50,
      },
    }).as('getAnalysisStatus');
    
    cy.intercept('GET', '/api/analysis/history*', {
      statusCode: 200,
      body: {
        analyses: [
          {
            id: 'analysis-456',
            user_id: '1',
            stock_code: '000002',
            market_type: 'CN',
            status: 'completed',
            progress: 100,
            created_at: new Date(Date.now() - 86400000).toISOString(),
            completed_at: new Date().toISOString(),
            result_data: {
              summary: '分析完成',
              recommendations: ['买入'],
            },
          },
        ],
        page: 1,
        limit: 20,
        total: 1,
      },
    }).as('getAnalysisHistory');
    
    // Login first
    cy.login('testuser', 'password123');
  });

  it('should navigate to analysis page and display tabs', () => {
    cy.visit('/analysis');
    
    // Check page title
    cy.contains('股票分析平台').should('be.visible');
    
    // Check tabs
    cy.contains('分析与结果').should('be.visible');
    cy.contains('实时进度').should('be.visible');
    cy.contains('历史记录').should('be.visible');
    
    // Should be on analysis tab by default
    cy.get('[data-testid="analysis-form"]').should('be.visible');
    cy.get('[data-testid="analysis-results"]').should('be.visible');
  });

  it('should start analysis and switch to progress tab', () => {
    cy.visit('/analysis');
    
    // Fill analysis form
    cy.get('[data-testid="stock-code-input"]').type('000001');
    cy.get('[data-testid="market-type-select"]').click();
    cy.contains('CN').click();
    cy.get('[data-testid="analysis-date-picker"]').click();
    cy.get('.ant-picker-today-btn').click();
    
    // Select analysts
    cy.get('[data-testid="analysts-checkbox-fundamentals"]').check();
    cy.get('[data-testid="analysts-checkbox-technical"]').check();
    
    // Start analysis
    cy.get('[data-testid="start-analysis-button"]').click();
    
    // Wait for API call
    cy.wait('@startAnalysis');
    
    // Should switch to progress tab automatically
    cy.get('[data-testid="progress-dashboard"]').should('be.visible');
    cy.contains('Analysis ID: analysis-123').should('be.visible');
    
    // Progress indicator should be visible in tab
    cy.get('.progress-indicator').should('be.visible');
  });

  it('should display analysis progress updates', () => {
    // Mock progressive status updates
    let progressValue = 0;
    cy.intercept('GET', '/api/analysis/*/status', (req) => {
      progressValue += 25;
      req.reply({
        statusCode: 200,
        body: {
          id: 'analysis-123',
          status: progressValue >= 100 ? 'completed' : 'running',
          progress: Math.min(progressValue, 100),
          result_data: progressValue >= 100 ? { summary: '分析完成' } : null,
        },
      });
    }).as('progressUpdate');
    
    cy.visit('/analysis');
    
    // Start analysis (assuming form is filled)
    cy.get('[data-testid="start-analysis-button"]').click();
    cy.wait('@startAnalysis');
    
    // Should show progress updates
    cy.wait('@progressUpdate');
    cy.contains('25%').should('be.visible');
    
    cy.wait('@progressUpdate');
    cy.contains('50%').should('be.visible');
    
    cy.wait('@progressUpdate');
    cy.contains('75%').should('be.visible');
    
    cy.wait('@progressUpdate');
    cy.contains('100%').should('be.visible');
    cy.contains('分析完成').should('be.visible');
  });

  it('should cancel running analysis', () => {
    cy.intercept('POST', '/api/analysis/*/cancel', {
      statusCode: 200,
      body: { message: 'Analysis cancelled' },
    }).as('cancelAnalysis');
    
    cy.visit('/analysis');
    
    // Start analysis
    cy.get('[data-testid="start-analysis-button"]').click();
    cy.wait('@startAnalysis');
    
    // Should be on progress tab
    cy.get('[data-testid="progress-dashboard"]').should('be.visible');
    
    // Cancel analysis
    cy.get('[data-testid="cancel-analysis-button"]').click();
    
    // Confirm cancellation
    cy.get('.ant-modal-confirm-btns .ant-btn-primary').click();
    
    cy.wait('@cancelAnalysis');
    
    // Should return to analysis tab
    cy.get('[data-testid="analysis-form"]').should('be.visible');
  });

  it('should display analysis history', () => {
    cy.visit('/analysis');
    
    // Click history tab
    cy.contains('历史记录').click();
    
    // Wait for history to load
    cy.wait('@getAnalysisHistory');
    
    // Check history content
    cy.contains('分析历史').should('be.visible');
    cy.contains('000002').should('be.visible');
    cy.contains('completed').should('be.visible');
    cy.contains('分析完成').should('be.visible');
  });

  it('should handle empty analysis history', () => {
    // Mock empty history
    cy.intercept('GET', '/api/analysis/history*', {
      statusCode: 200,
      body: {
        analyses: [],
        page: 1,
        limit: 20,
        total: 0,
      },
    }).as('emptyHistory');
    
    cy.visit('/analysis');
    
    // Click history tab
    cy.contains('历史记录').click();
    
    cy.wait('@emptyHistory');
    
    // Should show empty message
    cy.contains('暂无历史分析记录').should('be.visible');
  });

  it('should handle analysis errors', () => {
    // Mock analysis error
    cy.intercept('POST', '/api/analysis/start', {
      statusCode: 400,
      body: { message: '股票代码无效' },
    }).as('analysisError');
    
    cy.visit('/analysis');
    
    // Try to start analysis with invalid data
    cy.get('[data-testid="start-analysis-button"]').click();
    
    cy.wait('@analysisError');
    
    // Should show error message
    cy.contains('股票代码无效').should('be.visible');
    
    // Should stay on analysis tab
    cy.get('[data-testid="analysis-form"]').should('be.visible');
  });

  it('should validate analysis form', () => {
    cy.visit('/analysis');
    
    // Try to submit empty form
    cy.get('[data-testid="start-analysis-button"]').click();
    
    // Should show validation errors
    cy.contains('请输入股票代码').should('be.visible');
    cy.contains('请选择市场类型').should('be.visible');
    cy.contains('请选择分析日期').should('be.visible');
    cy.contains('请至少选择一个分析师').should('be.visible');
  });

  it('should handle network errors gracefully', () => {
    // Mock network error
    cy.intercept('POST', '/api/analysis/start', {
      forceNetworkError: true,
    }).as('networkError');
    
    cy.visit('/analysis');
    
    // Fill form and submit
    cy.get('[data-testid="stock-code-input"]').type('000001');
    cy.get('[data-testid="start-analysis-button"]').click();
    
    cy.wait('@networkError');
    
    // Should show error message
    cy.contains('网络错误').should('be.visible');
  });

  it('should persist analysis state across page refreshes', () => {
    cy.visit('/analysis');
    
    // Start analysis
    cy.get('[data-testid="start-analysis-button"]').click();
    cy.wait('@startAnalysis');
    
    // Should be on progress tab
    cy.get('[data-testid="progress-dashboard"]').should('be.visible');
    
    // Refresh page
    cy.reload();
    
    // Should still show progress (assuming state is persisted)
    cy.get('[data-testid="progress-dashboard"]').should('be.visible');
    cy.contains('Analysis ID: analysis-123').should('be.visible');
  });

  it('should handle concurrent analysis attempts', () => {
    // Mock concurrent analysis error
    cy.intercept('POST', '/api/analysis/start', {
      statusCode: 409,
      body: { message: '已有分析任务在进行中' },
    }).as('concurrentError');
    
    cy.visit('/analysis');
    
    // Try to start analysis
    cy.get('[data-testid="start-analysis-button"]').click();
    
    cy.wait('@concurrentError');
    
    // Should show error message
    cy.contains('已有分析任务在进行中').should('be.visible');
  });
});