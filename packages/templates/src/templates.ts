import type { TemplateMeta } from "./types";
import { createDraftSpec } from "@metaagent/spec";
import { chatbotInterview, genericAgentInterview } from "@metaagent/interview";
import { ulid } from "ulid";

export const chatbotTemplate: TemplateMeta = {
  id: "chatbot",
  name: "Chatbot",
  description: "Create a conversational AI chatbot for customer support, FAQ, or general chat",
  category: "chatbot",
  tags: ["conversation", "support", "chat"],
  interview: chatbotInterview,
  defaultSpec: createDraftSpec({
    title: "My Chatbot",
    payload: {
      specVersion: "0.1.0" as const,
      meta: {
        id: ulid(),
        name: "my-chatbot",
        description: "A friendly chatbot assistant",
        version: "1.0.0",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      variables: [],
      prompt: {
        template: "You are a helpful and friendly chatbot assistant. Answer questions clearly and helpfully.",
      },
      model: {
        provider: "openai",
        model: "gpt-4",
        config: {
          temperature: 0.7,
          maxTokens: 1000,
        },
      },
      tools: [],
      limits: {
        timeoutSec: 30,
        budgetUsd: 10,
      },
    },
  }),
};

export const webAutomationTemplate: TemplateMeta = {
  id: "web-automation",
  name: "Web Automation Agent",
  description: "Automate web tasks like form filling, data extraction, and browser interactions",
  category: "web-automation",
  tags: ["automation", "web", "scraping", "forms"],
  interview: genericAgentInterview,
  defaultSpec: createDraftSpec({
    title: "Web Automation Agent",
    payload: {
      specVersion: "0.1.0" as const,
      meta: {
        id: ulid(),
        name: "web-automation-agent",
        description: "Automate web-based tasks",
        version: "1.0.0",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      variables: [
        {
          key: "target-url",
          name: "Target URL",
          type: "string",
          description: "The website URL to automate",
          required: true,
        },
      ],
      prompt: {
        template: "You are a web automation specialist. Navigate to {{target-url}} and perform the requested automation tasks efficiently and accurately.",
      },
      model: {
        provider: "openai",
        model: "gpt-4",
        config: {
          temperature: 0.3,
          maxTokens: 2000,
        },
      },
      tools: [
        {
          kind: "http",
          allowDomains: ["https://example.com"], // Example allowed domain
        },
      ],
      limits: {
        timeoutSec: 120,
        budgetUsd: 20,
      },
    },
  }),
};

export const apiCopilotTemplate: TemplateMeta = {
  id: "api-copilot",
  name: "API Copilot",
  description: "Help users interact with APIs, generate code, and troubleshoot API issues",
  category: "api-copilot",
  tags: ["api", "development", "coding", "debugging"],
  interview: genericAgentInterview,
  defaultSpec: createDraftSpec({
    title: "API Copilot",
    payload: {
      specVersion: "0.1.0" as const,
      meta: {
        id: ulid(),
        name: "api-copilot",
        description: "Expert assistant for API development and integration",
        version: "1.0.0",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      variables: [
        {
          key: "api-docs",
          name: "API Documentation",
          type: "string",
          description: "Link to API documentation or OpenAPI spec",
          required: false,
        },
      ],
      prompt: {
        template: "You are an expert API development assistant. Help users with API integration, code generation, debugging, and best practices. Reference the API docs: {{api-docs}}",
      },
      model: {
        provider: "openai",
        model: "gpt-4",
        config: {
          temperature: 0.2,
          maxTokens: 3000,
        },
      },
      tools: [
        {
          kind: "http",
          allowDomains: ["https://api.example.com"], // Example API domain
        },
        {
          kind: "code-interpreter",
          timeoutSec: 30,
        },
      ],
      limits: {
        timeoutSec: 60,
        budgetUsd: 15,
      },
    },
  }),
};

export const templates: TemplateMeta[] = [
  chatbotTemplate,
  webAutomationTemplate,
  apiCopilotTemplate,
];
