// Jest configuration wired through next/jest so tests share the same SWC
// transform, module aliases (@/*) and env handling as the Next.js build.
// jsdom gives us a real DOM, so component tests can simulate user clicks and
// assert on the resulting UI — a genuine interaction test, not a source scan.
const nextJest = require('next/jest')

const createJestConfig = nextJest({ dir: './' })

/** @type {import('jest').Config} */
const customJestConfig = {
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: ['**/*.test.ts', '**/*.test.tsx'],
}

module.exports = createJestConfig(customJestConfig)
