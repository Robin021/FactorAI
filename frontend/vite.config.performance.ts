/**
 * Vite 性能优化配置
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    react({
      // 启用 React Fast Refresh
      fastRefresh: true,
    }),
  ],
  
  // 构建优化
  build: {
    // 启用代码分割
    rollupOptions: {
      output: {
        // 手动分包
        manualChunks: {
          // 第三方库单独打包
          vendor: ['react', 'react-dom', 'react-router-dom'],
          antd: ['antd', '@ant-design/icons'],
          charts: ['echarts', 'echarts-for-react'],
          utils: ['axios', 'dayjs', 'lodash'],
        },
        // 文件名包含hash
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || [];
          let extType = info[info.length - 1];
          
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name || '')) {
            extType = 'media';
          } else if (/\.(png|jpe?g|gif|svg)(\?.*)?$/i.test(assetInfo.name || '')) {
            extType = 'img';
          } else if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name || '')) {
            extType = 'fonts';
          }
          
          return `${extType}/[name]-[hash].[ext]`;
        },
      },
    },
    
    // 压缩配置
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 生产环境移除console
        drop_debugger: true,
      },
    },
    
    // 启用 gzip 压缩
    reportCompressedSize: true,
    
    // 设置chunk大小警告阈值
    chunkSizeWarningLimit: 1000,
    
    // 启用 CSS 代码分割
    cssCodeSplit: true,
  },
  
  // 开发服务器优化
  server: {
    // 启用 HMR
    hmr: true,
    // 预构建优化
    force: false,
  },
  
  // 依赖预构建优化
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'antd',
      'echarts',
      'axios',
      'dayjs',
      'lodash',
    ],
    // 排除不需要预构建的依赖
    exclude: ['@vitejs/plugin-react'],
  },
  
  // 路径别名
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@pages': resolve(__dirname, 'src/pages'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@hooks': resolve(__dirname, 'src/hooks'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@types': resolve(__dirname, 'src/types'),
    },
  },
  
  // CSS 优化
  css: {
    // CSS 模块化
    modules: {
      localsConvention: 'camelCase',
    },
    // PostCSS 配置
    postcss: {
      plugins: [
        // 自动添加浏览器前缀
        require('autoprefixer'),
        // CSS 压缩
        require('cssnano')({
          preset: 'default',
        }),
      ],
    },
  },
  
  // 实验性功能
  experimental: {
    // 启用构建时优化
    renderBuiltUrl: (filename) => {
      // CDN 配置示例
      if (process.env.NODE_ENV === 'production') {
        return `https://cdn.example.com/${filename}`;
      }
      return `/${filename}`;
    },
  },
  
  // 环境变量
  define: {
    __DEV__: process.env.NODE_ENV === 'development',
    __PROD__: process.env.NODE_ENV === 'production',
  },
});