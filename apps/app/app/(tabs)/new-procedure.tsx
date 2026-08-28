import { colonoscopyWorkflowSteps } from "@phd-ass/domain";
import { ScreenContainer, SectionCard, StatusPill } from "@phd-ass/ui";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { asTextStyle, asViewStyle } from "../../lib/style-casts";

export default function NewProcedureScreen() {
  return (
    <ScreenContainer>
      <SectionCard
        title="New Procedure"
        subtitle="Colonoscopy is locked as the first live workflow for V1."
      >
        <StatusPill label="Procedure: Colonoscopy" />
        <Text style={asTextStyle(styles.text)}>
          This screen will become the entry point for case creation, patient lookup, and staff assignment.
        </Text>
      </SectionCard>

      <SectionCard title="Workflow steps" subtitle="Pulled from the shared domain package.">
        {colonoscopyWorkflowSteps.map((step, index) => (
          <View key={step.id} style={asViewStyle(styles.stepRow)}>
            <Text style={asTextStyle(styles.stepNumber)}>{index + 1}</Text>
            <View style={asViewStyle(styles.stepCopy)}>
              <Text style={asTextStyle(styles.stepTitle)}>{step.label}</Text>
              <Text style={asTextStyle(styles.stepDescription)}>{step.description}</Text>
            </View>
          </View>
        ))}
      </SectionCard>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  text: {
    color: "#5d7288",
    lineHeight: 20
  },
  stepRow: {
    flexDirection: "row" as const,
    gap: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#d6dfe8"
  },
  stepNumber: {
    width: 24,
    fontWeight: "700" as const,
    color: "#0a5d6b"
  },
  stepCopy: {
    flex: 1,
    gap: 2
  },
  stepTitle: {
    fontWeight: "700" as const,
    color: "#17324d"
  },
  stepDescription: {
    color: "#5d7288"
  }
});
