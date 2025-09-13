import type { TemplateMeta } from "./types";
import { createDraftSpec } from "@metaagent/spec";
import { chatbotInterview, genericAgentInterview } from "@metaagent/interview";

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
        id: "temp-id",
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
        name: "gpt-4",
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
        id: "temp-id",
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
        name: "gpt-4",
        config: {
          temperature: 0.3,
          maxTokens: 2000,
        },
      },
      tools: [
        {
          id: "web-browser",
          name: "Web Browser",
          description: "Navigate and interact with web pages",
          type: "function",
          config: {
            function: {
              name: "web_browser",
              description: "Navigate to URLs, click elements, fill forms",
              parameters: {
                type: "object",
                properties: {
                  action: { type: "string", enum: ["navigate", "click", "fill", "extract"] },
                  target: { type: "string" },
                  value: { type: "string" },
                },
                required: ["action"],
              },
            },
          },
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
        id: "temp-id",
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
        name: "gpt-4",
        config: {
          temperature: 0.2,
          maxTokens: 3000,
        },
      },
      tools: [
        {
          id: "http-client",
          name: "HTTP Client",
          description: "Make HTTP requests to test APIs",
          type: "function",
          config: {
            function: {
              name: "http_request",
              description: "Make HTTP requests with various methods",
              parameters: {
                type: "object",
                properties: {
                  method: { type: "string", enum: ["GET", "POST", "PUT", "DELETE", "PATCH"] },
                  url: { type: "string" },
                  headers: { type: "object" },
                  body: { type: "string" },
                },
                required: ["method", "url"],
              },
            },
          },
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
