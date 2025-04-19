import { Command } from 'commander';

export function runCLI(argv) {
  const program = new Command();

  program
    .name('task-master')
    .version('0.0.1')
    .description('AI-driven development task management');

  // TODO: add commands (list, show, expand, set-status, etc.)

  program.parse(argv);
}
