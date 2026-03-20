/**
 * Card registration utility.
 * Registers custom cards with Home Assistant's card type system via window.customCards.
 */

export interface CustomCardRegistration {
  type: string;
  name: string;
  description?: string;
  documentationURL?: string;
  preview?: boolean;
  default?: Record<string, unknown>;
}

declare global {
  interface Window {
    customCards?: CustomCardRegistration[];
  }
}

export function registerCustomCard(card: CustomCardRegistration): void {
  if (typeof window !== 'undefined') {
    if (!window.customCards) {
      window.customCards = [];
    }
    // Avoid duplicate registration by type
    const existing = window.customCards.findIndex((c) => c.type === card.type);
    if (existing >= 0) {
      window.customCards[existing] = card;
    } else {
      window.customCards.push(card);
    }
  }
}
