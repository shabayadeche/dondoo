import { sampleTasks } from "@phd-ass/domain";
import { ScreenContainer, SectionCard, StatusPill } from "@phd-ass/ui";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { asTextStyle, asViewStyle } from "../../lib/style-casts";

export default function TasksScreen() {
  return (
    <ScreenContainer>
      <SectionCard title="Follow-Up Tasks" subtitle="Clinical tasks stay in the clinical service in V1.">
        {sampleTasks.map((task) => (
          <View key={task.id} style={asViewStyle(styles.taskRow)}>
            <View style={asViewStyle(styles.taskCopy)}>
              <Text style={asTextStyle(styles.taskTitle)}>{task.type}</Text>
              <Text style={asTextStyle(styles.taskMeta)}>
                {task.ownerName} - Case {task.caseId}
              </Text>
            </View>
            <StatusPill label={task.status} />
          </View>
        ))}
      </SectionCard>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  taskRow: {
    flexDirection: "row" as const,
    justifyContent: "space-between" as const,
    alignItems: "center" as const,
    gap: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#d6dfe8"
  },
  taskCopy: {
    flex: 1,
    gap: 2
  },
  taskTitle: {
    fontWeight: "700" as const,
    color: "#17324d"
  },
  taskMeta: {
    color: "#5d7288"
  }
});
