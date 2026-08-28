import { ScreenContainer, SectionCard } from "@phd-ass/ui";
import React from "react";
import { StyleSheet, Text } from "react-native";
import { asTextStyle } from "../../lib/style-casts";

export default function ReportsScreen() {
  return (
    <ScreenContainer>
      <SectionCard
        title="Reports"
        subtitle="Finalized reports and PDFs will surface here once the API persistence layer is wired."
      >
        <Text style={asTextStyle(styles.bodyText)}>
          The hybrid design keeps the canonical finalized note and PDF snapshot in the clinical service. Odoo can
          receive copies later for admin visibility.
        </Text>
      </SectionCard>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  bodyText: {
    color: "#5d7288",
    lineHeight: 20
  }
});
