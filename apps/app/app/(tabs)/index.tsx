import { appConfig } from "@phd-ass/config";
import { dashboardSnapshot, sampleCases } from "@phd-ass/domain";
import { MetricTile, ScreenContainer, SectionCard, StatusPill } from "@phd-ass/ui";
import { Link } from "expo-router";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { asLinkStyle, asTextStyle, asViewStyle } from "../../lib/style-casts";

export default function DashboardScreen() {
  return (
    <ScreenContainer>
      <SectionCard
        title={appConfig.appName}
        subtitle="Hybrid self-hosted scaffold for colonoscopy-first reporting."
      >
        <StatusPill label="Colonoscopy MVP" />
        <Text style={asTextStyle(styles.bodyText)}>
          This shell is wired to the shared domain package and mirrors the build-ready documentation baseline.
        </Text>
      </SectionCard>

      <View style={asViewStyle(styles.metricGrid)}>
        <MetricTile label="Active drafts" value={dashboardSnapshot.activeDrafts} />
        <MetricTile label="Open tasks" value={dashboardSnapshot.openTasks} />
        <MetricTile label="Finalized today" value={dashboardSnapshot.finalizedToday} />
      </View>

      <SectionCard title="Recent cases" subtitle="Sample domain data wired through the shared package.">
        {sampleCases.map((entry) => (
          <Link href={`/case/${entry.id}`} key={entry.id} style={asLinkStyle(styles.caseRow)}>
            <Text style={asTextStyle(styles.caseTitle)}>{entry.patientIdentifier}</Text>
            <Text style={asTextStyle(styles.caseMeta)}>
              {entry.endoscopistName} - {entry.status}
            </Text>
          </Link>
        ))}
      </SectionCard>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  metricGrid: {
    gap: 12
  },
  bodyText: {
    color: "#5d7288",
    lineHeight: 20
  },
  caseRow: {
    display: "flex" as const,
    gap: 4,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#d6dfe8"
  },
  caseTitle: {
    fontSize: 16,
    fontWeight: "700" as const,
    color: "#17324d"
  },
  caseMeta: {
    color: "#5d7288"
  }
});
