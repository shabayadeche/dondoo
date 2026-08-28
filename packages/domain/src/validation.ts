import { z } from "zod";
import { caseStatuses, procedureTypes, sexOptions, taskStatuses, taskTypes } from "./enums.js";

export const startCaseSchema = z.object({
  procedureType: z.enum(procedureTypes),
  patientIdentifier: z.string().min(1),
  procedureDatetime: z.string().min(1),
  dobOrAge: z.string().min(1),
  sex: z.enum(sexOptions),
  facilityUnit: z.string().min(1),
  endoscopistUserId: z.string().min(1),
  referrerService: z.string().optional(),
  assistantNurseUserId: z.string().optional()
});

export const sharedSafetySchema = z.object({
  indication: z.string().min(1),
  priority: z.enum(["elective", "urgent", "emergency"]),
  asaClass: z.enum(["I", "II", "III", "IV", "V"]),
  antithromboticPlan: z.enum(["na", "continue", "hold", "bridging_other"]),
  consentDocumented: z.boolean(),
  teamPauseCompleted: z.boolean(),
  sedationAnesthesia: z.string().min(1)
});

export const lesionSchema = z.object({
  location: z.string().min(1),
  sizeMm: z.number().int().nonnegative(),
  morphology: z.string().min(1),
  resectionMethod: z.string().min(1),
  completeResection: z.boolean(),
  retrieved: z.boolean(),
  specimenContainerRef: z.string().optional()
});

export const followUpTaskSchema = z.object({
  id: z.string().min(1),
  caseId: z.string().min(1),
  type: z.enum(taskTypes),
  status: z.enum(taskStatuses),
  ownerName: z.string().min(1),
  dueDate: z.string().optional()
});

export const caseSummarySchema = z.object({
  id: z.string().min(1),
  patientIdentifier: z.string().min(1),
  procedureType: z.enum(procedureTypes),
  status: z.enum(caseStatuses),
  procedureDatetime: z.string().min(1),
  endoscopistName: z.string().min(1)
});
