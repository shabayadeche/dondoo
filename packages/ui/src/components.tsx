import type { ComponentProps, PropsWithChildren } from "react";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, radius, spacing } from "./tokens.js";

function asTextStyle(style: unknown): ComponentProps<typeof Text>["style"] {
  return style as ComponentProps<typeof Text>["style"];
}

function asViewStyle(style: unknown): ComponentProps<typeof View>["style"] {
  return style as ComponentProps<typeof View>["style"];
}

export function ScreenContainer({ children }: PropsWithChildren) {
  return <View style={asViewStyle(styles.screen)}>{children}</View>;
}

export function SectionCard({
  title,
  subtitle,
  children
}: PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <View style={asViewStyle(styles.card)}>
      <Text style={asTextStyle(styles.cardTitle)}>{title}</Text>
      {subtitle ? <Text style={asTextStyle(styles.cardSubtitle)}>{subtitle}</Text> : null}
      <View style={asViewStyle(styles.cardBody)}>{children}</View>
    </View>
  );
}

export function StatusPill({ label }: { label: string }) {
  return (
    <View style={asViewStyle(styles.pill)}>
      <Text style={asTextStyle(styles.pillText)}>{label}</Text>
    </View>
  );
}

export function MetricTile({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={asViewStyle(styles.metricTile)}>
      <Text style={asTextStyle(styles.metricLabel)}>{label}</Text>
      <Text style={asTextStyle(styles.metricValue)}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.md,
    gap: spacing.md
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.line,
    gap: spacing.sm
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "700" as const,
    color: colors.ink
  },
  cardSubtitle: {
    fontSize: 13,
    color: colors.inkSoft
  },
  cardBody: {
    gap: spacing.sm
  },
  pill: {
    alignSelf: "flex-start" as const,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "#e5f6f4"
  },
  pillText: {
    color: colors.accentDeep,
    fontWeight: "700" as const,
    fontSize: 12
  },
  metricTile: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.xs
  },
  metricLabel: {
    fontSize: 12,
    textTransform: "uppercase" as const,
    color: colors.inkSoft
  },
  metricValue: {
    fontSize: 22,
    fontWeight: "700" as const,
    color: colors.ink
  }
});
