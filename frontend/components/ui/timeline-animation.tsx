import type React from "react";

type TimelineContentProps<T extends React.ElementType> = {
  as?: T;
  children?: React.ReactNode;
  className?: string;
  animationNum?: number;
  timelineRef?: React.RefObject<HTMLElement | null>;
  customVariants?: unknown;
  once?: boolean;
} & Omit<React.ComponentPropsWithoutRef<T>, "as" | "children" | "className">;

export function TimelineContent<T extends React.ElementType = "div">({
  as,
  children,
  className,
  ...props
}: TimelineContentProps<T>) {
  const Component = (as ?? "div") as React.ElementType;

  return (
    <Component className={className} {...props}>
      {children}
    </Component>
  );
}
