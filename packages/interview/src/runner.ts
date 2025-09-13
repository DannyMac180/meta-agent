import type { InterviewScript, InterviewState, InterviewNode, RunNodeResult, InterviewEvent } from "./types";
import { updateDraftSpec } from "@metaagent/spec";

export class InterviewRunner {
  private script: InterviewScript;
  private maxNodes = 100; // Cycle detection

  constructor(script: InterviewScript) {
    this.script = script;
  }

  runNode(state: InterviewState, answer?: any): RunNodeResult {
    const events: InterviewEvent[] = [];
    
    // Cycle detection
    if (state.visitedNodes.length > this.maxNodes) {
      throw new Error("Interview cycle detected: too many nodes visited");
    }

    const currentNode = this.script.nodes[state.currentNodeId];
    if (!currentNode) {
      throw new Error(`Node not found: ${state.currentNodeId}`);
    }

    // Process answer if provided
    let updatedState = { ...state };
    if (answer !== undefined && currentNode.type === "question") {
      // Validate answer
      if (currentNode.validate && !currentNode.validate(answer)) {
        throw new Error(`Invalid answer for node ${currentNode.id}`);
      }

      // Store answer
      updatedState.answers = {
        ...updatedState.answers,
        [currentNode.id]: answer,
      };

      // Map to spec field
      updatedState.specDraft = this.updateSpecFromAnswer(
        updatedState.specDraft,
        currentNode.field,
        answer
      );

      events.push({
        type: "answer_changed",
        nodeId: currentNode.id,
        timestamp: Date.now(),
        data: { answer, field: currentNode.field },
      });
    }

    // Determine next node
    let nextNodeId: string | null = null;
    
    switch (currentNode.type) {
      case "question":
        // Find next node (simple linear progression for now)
        const nodeIds = Object.keys(this.script.nodes);
        const currentIndex = nodeIds.indexOf(state.currentNodeId);
        if (currentIndex >= 0 && currentIndex < nodeIds.length - 1) {
          nextNodeId = nodeIds[currentIndex + 1];
        } else {
          nextNodeId = "end";
        }
        break;
        
      case "branch":
        if (currentNode.condition(updatedState.answers)) {
          nextNodeId = currentNode.next;
        } else {
          // Find next node after branch
          const nodeIds = Object.keys(this.script.nodes);
          const currentIndex = nodeIds.indexOf(state.currentNodeId);
          if (currentIndex >= 0 && currentIndex < nodeIds.length - 1) {
            nextNodeId = nodeIds[currentIndex + 1];
          } else {
            nextNodeId = "end";
          }
        }
        break;
        
      case "end":
        events.push({
          type: "interview_completed",
          nodeId: currentNode.id,
          timestamp: Date.now(),
        });
        break;
    }

    // Update state with next node
    if (nextNodeId) {
      updatedState.currentNodeId = nextNodeId;
      updatedState.visitedNodes = [...updatedState.visitedNodes, state.currentNodeId];
      
      events.push({
        type: "node_visited",
        nodeId: nextNodeId,
        timestamp: Date.now(),
      });
    }

    return {
      nextNodeId,
      updatedState,
      events,
    };
  }

  private updateSpecFromAnswer(specDraft: any, field: string, value: any): any {
    const fieldPath = field.split(".");
    const updated = JSON.parse(JSON.stringify(specDraft));
    
    // Navigate to the nested field and set value
    let current = updated.payload;
    if (!current) {
      updated.payload = {};
      current = updated.payload;
    }

    for (let i = 0; i < fieldPath.length - 1; i++) {
      if (!current[fieldPath[i]]) {
        current[fieldPath[i]] = {};
      }
      current = current[fieldPath[i]];
    }
    
    current[fieldPath[fieldPath.length - 1]] = value;
    
    return updateDraftSpec(specDraft, { payload: updated.payload });
  }

  getCurrentNode(state: InterviewState): InterviewNode {
    const node = this.script.nodes[state.currentNodeId];
    if (!node) {
      throw new Error(`Node not found: ${state.currentNodeId}`);
    }
    return node;
  }

  isComplete(state: InterviewState): boolean {
    return state.currentNodeId === "end";
  }
}
