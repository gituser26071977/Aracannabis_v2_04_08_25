/**
 * json — utility for safe JSON.stringify with consistent indentation.
 */

export const toJson = (value: unknown): string => JSON.stringify(value, null, 2);
