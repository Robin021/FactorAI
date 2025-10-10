import React from 'react';
import { Breadcrumb, Space, Typography } from 'antd';
import type { BreadcrumbProps } from 'antd';
import './PageHeader.css';

interface CrumbItem {
  title: React.ReactNode;
  href?: string;
  onClick?: () => void;
}

interface PageHeaderProps {
  title: React.ReactNode;
  subTitle?: React.ReactNode;
  breadcrumbItems?: CrumbItem[];
  extra?: React.ReactNode;
  children?: React.ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subTitle,
  breadcrumbItems,
  extra,
  children,
}) => {
  const breadcrumb: BreadcrumbProps | undefined = breadcrumbItems
    ? {
        items: breadcrumbItems.map((item) => ({
          title: (
            <a href={item.href} onClick={item.onClick}>
              {item.title}
            </a>
          ),
        })),
      }
    : undefined;

  return (
    <div className="page-header">
      <div className="page-header-top">
        {breadcrumb && <Breadcrumb {...breadcrumb} />}
        {extra && <div className="page-header-actions">{extra}</div>}
      </div>
      <div className="page-header-main">
        <Space direction="vertical" size={4}>
          <Typography.Title level={2} style={{ margin: 0 }}>
            {title}
          </Typography.Title>
          {subTitle && (
            <Typography.Text type="secondary">{subTitle}</Typography.Text>
          )}
        </Space>
        {children}
      </div>
    </div>
  );
};

export default PageHeader;

