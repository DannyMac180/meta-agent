import { describe, it, expect } from 'vitest';
import { InterviewRunner } from './runner';
import { genericAgentInterview } from './scripts';
import { createDraftSpec } from '@metaagent/spec';

describe('InterviewRunner', () => {
  it('should create a runner with a script', () => {
    const runner = new InterviewRunner(genericAgentInterview);
    expect(runner).toBeInstanceOf(InterviewRunner);
  });

  it('should get the current node', () => {
    const runner = new InterviewRunner(genericAgentInterview);
    const state = {
      answers: {},
      currentNodeId: 'agent-name',
      specDraft: createDraftSpec({ title: 'Test Agent' }),
      visitedNodes: [],
    };

    const currentNode = runner.getCurrentNode(state);
    expect(currentNode.id).toBe('agent-name');
    expect(currentNode.type).toBe('question');
  });

  it('should detect cycle when too many nodes visited', () => {
    const runner = new InterviewRunner(genericAgentInterview);
    const state = {
      answers: {},
      currentNodeId: 'agent-name',
      specDraft: createDraftSpec({ title: 'Test Agent' }),
      visitedNodes: new Array(101).fill('test-node'),
    };

    expect(() => runner.runNode(state)).toThrow('Interview cycle detected');
  });

  it('should process question node with answer', () => {
    const runner = new InterviewRunner(genericAgentInterview);
    const state = {
      answers: {},
      currentNodeId: 'agent-name',
      specDraft: createDraftSpec({ title: 'Test Agent' }),
      visitedNodes: [],
    };

    const result = runner.runNode(state, 'My Test Agent');
    
    expect(result.updatedState.answers['agent-name']).toBe('My Test Agent');
    expect(result.events.length).toBeGreaterThan(0);
    expect(result.events[0].type).toBe('answer_changed');
  });

  it('should determine interview completion', () => {
    const runner = new InterviewRunner(genericAgentInterview);
    const endState = {
      answers: {},
      currentNodeId: 'end',
      specDraft: createDraftSpec({ title: 'Test Agent' }),
      visitedNodes: [],
    };

    expect(runner.isComplete(endState)).toBe(true);

    const activeState = {
      answers: {},
      currentNodeId: 'agent-name',
      specDraft: createDraftSpec({ title: 'Test Agent' }),
      visitedNodes: [],
    };

    expect(runner.isComplete(activeState)).toBe(false);
  });
});
