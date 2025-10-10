import React from 'react';
import { Drawer, List, Badge, Button, Typography, Empty, Tag } from 'antd';
import { 
  BellOutlined, 
  CheckOutlined, 
  DeleteOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { useNotificationStore, Notification } from '@/stores/notificationStore';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import './NotificationCenter.css';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const { Text } = Typography;

interface NotificationCenterProps {
  open: boolean;
  onClose: () => void;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ open, onClose }) => {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
  } = useNotificationStore();

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircleOutlined style={{ color: 'var(--success-color)' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: 'var(--warning-color)' }} />;
      default:
        return <InfoCircleOutlined style={{ color: 'var(--info-color)' }} />;
    }
  };

  const getTypeColor = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleMarkAsRead = (id: string) => {
    markAsRead(id);
  };

  const handleRemove = (id: string) => {
    removeNotification(id);
  };

  const renderNotificationItem = (notification: Notification) => (
    <List.Item
      key={notification.id}
      className={`notification-item ${!notification.read ? 'unread' : ''}`}
      actions={[
        !notification.read && (
          <Button
            type="text"
            size="small"
            icon={<CheckOutlined />}
            onClick={() => handleMarkAsRead(notification.id)}
            title="标记为已读"
          />
        ),
        <Button
          type="text"
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => handleRemove(notification.id)}
          title="删除"
        />,
      ].filter(Boolean)}
    >
      <List.Item.Meta
        avatar={getIcon(notification.type)}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Text strong={!notification.read}>{notification.title}</Text>
            <Tag color={getTypeColor(notification.type)}>
              {notification.type}
            </Tag>
            {!notification.read && (
              <Badge status="processing" />
            )}
          </div>
        }
        description={
          <div>
            {notification.message && (
              <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
                {notification.message}
              </Text>
            )}
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {dayjs(notification.timestamp).fromNow()}
            </Text>
          </div>
        }
      />
    </List.Item>
  );

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <BellOutlined />
            <span>通知中心</span>
            {unreadCount > 0 && (
              <Badge count={unreadCount} size="small" />
            )}
          </div>
          {notifications.length > 0 && (
            <div style={{ display: 'flex', gap: 8 }}>
              {unreadCount > 0 && (
                <Button size="small" onClick={markAllAsRead}>
                  全部已读
                </Button>
              )}
              <Button size="small" onClick={clearAll}>
                清空全部
              </Button>
            </div>
          )}
        </div>
      }
      placement="right"
      width={400}
      open={open}
      onClose={onClose}
      bodyStyle={{ padding: 0, maxHeight: 'calc(100vh - 64px)', overflow: 'auto' }}
    >
      {notifications.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无通知"
        />
      ) : (
        <List
          dataSource={notifications}
          renderItem={renderNotificationItem}
          className="notification-list"
        />
      )}
    </Drawer>
  );
};

// Hook for easier usage
export const useNotificationCenter = () => {
  const [open, setOpen] = React.useState(false);

  const showNotificationCenter = () => setOpen(true);
  const hideNotificationCenter = () => setOpen(false);

  const NotificationCenterComponent = () => (
    <NotificationCenter open={open} onClose={hideNotificationCenter} />
  );

  return {
    open,
    showNotificationCenter,
    hideNotificationCenter,
    NotificationCenter: NotificationCenterComponent,
  };
};

export default NotificationCenter;
