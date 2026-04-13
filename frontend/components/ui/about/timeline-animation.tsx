"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

type AnimationState = {
  y?: number;
  opacity?: number;
  filter?: string;
  transition?: {
    delay?: number;
    duration?: number;
    ease?: string;
  };
};

type AnimationVariants = {
  visible?: AnimationState | ((i: number) => AnimationState);
  hidden?: AnimationState;
};

type TimelineContentProps<T extends React.ElementType> = {
  as?: T;
  children?: React.ReactNode;
  className?: string;
  animationNum?: number;
  timelineRef?: React.RefObject<HTMLElement | null>;
  customVariants?: AnimationVariants;
  once?: boolean;
} & Omit<React.ComponentPropsWithoutRef<T>, "as" | "children" | "className">;

export function TimelineContent<T extends React.ElementType = "div">({
  as,
  children,
  className,
  animationNum = 0,
  timelineRef,
  customVariants,
  once = true,
  ...props
}: TimelineContentProps<T>) {
  const localRef = useRef<HTMLElement | null>(null);
  const [isVisible, setIsVisible] = useState<boolean>(() => !customVariants);
  void timelineRef;

  useEffect(() => {
    if (!customVariants) return;

    const node = localRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          if (once) {
            observer.unobserve(node);
          }
          return;
        }

        if (!once) {
          setIsVisible(false);
        }
      },
      {
        root: null,
        threshold: 0.15,
        rootMargin: "0px 0px -8% 0px",
      },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [customVariants, once]);

  const visibleState = useMemo(() => {
    const visible = customVariants?.visible;
    return typeof visible === "function" ? visible(animationNum) : visible;
  }, [customVariants, animationNum]);

  const hiddenState = customVariants?.hidden;
  const activeState = isVisible ? visibleState : hiddenState;

  const existingStyle = (props as { style?: React.CSSProperties }).style;
  const domProps = {
    ...(props as React.ComponentPropsWithoutRef<T> & { style?: React.CSSProperties }),
  };
  delete (domProps as { style?: React.CSSProperties }).style;

  const animationStyle: React.CSSProperties | undefined = customVariants
    ? {
        ...existingStyle,
        opacity: activeState?.opacity ?? existingStyle?.opacity,
        filter: activeState?.filter ?? existingStyle?.filter,
        transform:
          typeof activeState?.y === "number"
            ? `translate3d(0, ${activeState.y}px, 0)`
            : existingStyle?.transform,
        transitionProperty: "opacity, transform, filter",
        transitionDuration: `${visibleState?.transition?.duration ?? 0.65}s`,
        transitionTimingFunction:
          visibleState?.transition?.ease ?? "cubic-bezier(0.22, 1, 0.36, 1)",
        transitionDelay: isVisible ? `${visibleState?.transition?.delay ?? 0}s` : "0s",
        willChange: "opacity, transform, filter",
      }
    : existingStyle;

  const Component = (as ?? "div") as React.ElementType;

  return (
    <Component
      ref={localRef}
      className={className}
      style={animationStyle}
      {...domProps}
    >
      {children}
    </Component>
  );
}