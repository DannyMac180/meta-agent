import type { z } from "zod";
import type { AcceptanceEvalSchema } from "../validators/eval.js";

export type AcceptanceEval = z.infer<typeof AcceptanceEvalSchema>;
export type AcceptanceEvalAssertion = AcceptanceEval["assertions"][number];
