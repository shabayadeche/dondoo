import { sampleCases } from "@phd-ass/domain";
import { ScreenContainer, SectionCard, StatusPill } from "@phd-ass/ui";
import { useLocalSearchParams } from "expo-router";
import React from "react";
import { StyleSheet, Text } from "react-native";
import { asTextStyle } from "../../lib/style-casts";

export default function CaseDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const entry = sampleCases.find((candidate) => candidate.id === id);

  return (
    <ScreenContainer>
      <SectionCard title={`Case ${id ?? ""}`} subtitle="Clinical case detail placeholder.">
        {entry ? (
          <>
            <StatusPill label={entry.status} />
            <Text style={asTextStyle(styles.patientIdentifier)}>{entry.patientIdentifier}</Text>
            <Text style={asTextStyle(styles.secondaryText)}>{entry.endoscopistName}</Text>
            <Text style={asTextStyle(styles.secondaryText)}>{entry.procedureDatetime}</Text>
          </>
        ) : (
          <Text style={asTextStyle(styles.emptyState)}>No case found for the requested identifier.</Text>
        )}
      </SectionCard>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  patientIdentifier: {
    color: "#17324d",
    fontWeight: "700" as const
  },
  secondaryText: {
    color: "#5d7288"
  },
  emptyState: {
    color: "#5d7288"
  }
});
