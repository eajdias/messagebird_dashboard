"use client";

import { useEffect, useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

interface AnimatedNumberProps {
  value: number;
  decimals?: number;
}

export function AnimatedNumber({ value, decimals = 0 }: AnimatedNumberProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const motionValue = useMotionValue(mounted ? value : 0);
  const spring = useSpring(motionValue, { damping: 25, stiffness: 120 });
  const rounded = useTransform(spring, (v) => v.toFixed(decimals));

  useEffect(() => {
    if (mounted) motionValue.set(value);
  }, [value, motionValue, mounted]);

  if (!mounted) {
    return <span>{value.toFixed(decimals)}</span>;
  }

  return <motion.span>{rounded}</motion.span>;
}
