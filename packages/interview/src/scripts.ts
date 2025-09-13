import type { InterviewScript } from "./types";

// Generic interview script for all agent types
export const genericAgentInterview: InterviewScript = {
  id: "generic-agent",
  name: "Generic Agent Interview",
  startNodeId: "agent-name",
  nodes: {
    "agent-name": {
      type: "question",
      id: "agent-name",
      prompt: "What would you like to name your agent?",
      field: "meta.name",
      inputType: "text",
      required: true,
      validate: (value) => typeof value === "string" && value.length > 0,
    },
    "agent-description": {
      type: "question", 
      id: "agent-description",
      prompt: "Describe what your agent does",
      field: "meta.description",
      inputType: "textarea",
      required: false,
    },
    "agent-prompt": {
      type: "question",
      id: "agent-prompt",
      prompt: "What should be the main prompt/instruction for your agent?",
      field: "prompt.template",
      inputType: "textarea",
      required: true,
      validate: (value) => typeof value === "string" && value.length > 10,
    },
    "model-provider": {
      type: "question",
      id: "model-provider", 
      prompt: "Which AI model provider would you like to use?",
      field: "model.provider",
      inputType: "select",
      options: ["openai", "anthropic", "google"],
      required: true,
    },
    "budget-limit": {
      type: "question",
      id: "budget-limit",
      prompt: "Set a budget limit in USD (optional, leave empty for no limit)",
      field: "limits.budgetUsd",
      inputType: "number",
      required: false,
      validate: (value) => value === "" || (typeof value === "number" && value >= 0),
    },
    end: {
      type: "end",
      id: "end",
    },
  },
};

export const chatbotInterview: InterviewScript = {
  id: "chatbot",
  name: "Chatbot Interview",
  startNodeId: "chatbot-name",
  nodes: {
    "chatbot-name": {
      type: "question",
      id: "chatbot-name",
      prompt: "What should we call your chatbot?",
      field: "meta.name",
      inputType: "text",
      required: true,
    },
    "chatbot-personality": {
      type: "question",
      id: "chatbot-personality",
      prompt: "Describe your chatbot's personality and tone",
      field: "prompt.template",
      inputType: "textarea",
      required: true,
    },
    "knowledge-domain": {
      type: "question",
      id: "knowledge-domain",
      prompt: "What domain or topic should your chatbot be expert in?",
      field: "meta.description",
      inputType: "text",
      required: false,
    },
    end: {
      type: "end",
      id: "end",
    },
  },
};
