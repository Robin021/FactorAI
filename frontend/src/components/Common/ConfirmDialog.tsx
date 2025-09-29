import React from 'react';
import { Modal, Button, Typography } from 'antd';
import { ExclamationCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  content?: React.ReactNode;
  type?: 'warning' | 'danger' | 'info';
  okText?: string;
  cancelText?: string;
  loading?: boolean;
  onOk: () => void | Promise<void>;
  onCancel: () => void;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  content,
  type = 'warning',
  okText = '确定',
  cancelText = '取消',
  loading = false,
  onOk,
  onCancel,
}) => {
  const [confirmLoading, setConfirmLoading] = React.useState(false);

  const handleOk = async () => {
    setConfirmLoading(true);
    try {
      await onOk();
    } finally {
      setConfirmLoading(false);
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'danger':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'info':
        return <QuestionCircleOutlined style={{ color: '#1890ff' }} />;
      default:
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getOkButtonProps = () => {
    switch (type) {
      case 'danger':
        return { danger: true };
      case 'info':
        return { type: 'primary' as const };
      default:
        return { type: 'primary' as const };
    }
  };

  return (
    <Modal
      open={open}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {getIcon()}
          <span>{title}</span>
        </div>
      }
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          {cancelText}
        </Button>,
        <Button
          key="ok"
          {...getOkButtonProps()}
          loading={loading || confirmLoading}
          onClick={handleOk}
        >
          {okText}
        </Button>,
      ]}
    >
      {content && (
        <div style={{ marginTop: 16 }}>
          {typeof content === 'string' ? <Text>{content}</Text> : content}
        </div>
      )}
    </Modal>
  );
};

// Hook for easier usage
export const useConfirmDialog = () => {
  const [dialogState, setDialogState] = React.useState<{
    open: boolean;
    props: Omit<ConfirmDialogProps, 'open'>;
  }>({
    open: false,
    props: {
      title: '',
      onOk: () => {},
      onCancel: () => {},
    },
  });

  const showConfirm = (props: Omit<ConfirmDialogProps, 'open'>) => {
    setDialogState({
      open: true,
      props: {
        ...props,
        onCancel: () => {
          setDialogState((prev) => ({ ...prev, open: false }));
          props.onCancel?.();
        },
        onOk: async () => {
          await props.onOk();
          setDialogState((prev) => ({ ...prev, open: false }));
        },
      },
    });
  };

  const hideConfirm = () => {
    setDialogState((prev) => ({ ...prev, open: false }));
  };

  const ConfirmDialogComponent = () => (
    <ConfirmDialog open={dialogState.open} {...dialogState.props} />
  );

  return {
    showConfirm,
    hideConfirm,
    ConfirmDialog: ConfirmDialogComponent,
  };
};

export default ConfirmDialog;