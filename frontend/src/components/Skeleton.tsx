import styles from './Skeleton.module.css';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  style?: React.CSSProperties;
}

export default function Skeleton({ width, height, borderRadius, style }: SkeletonProps) {
  return (
    <div
      className={styles.skeleton}
      style={{
        width: width ?? '100%',
        height: height ?? 16,
        borderRadius: borderRadius ?? undefined,
        ...style,
      }}
    />
  );
}
