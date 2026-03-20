/**
 * PS-174: Card Registration Helper with documentationURL standard.
 *
 * Centralizes custom card registration with mandatory documentationURL.
 * All PilotSuite cards should use this helper for consistent metadata.
 *
 * Usage:
 *   registerCustomCard({
 *     type: 'styx-zone-creator-card',
 *     name: 'Styx Zone Creator',
 *     description: 'Create and manage Habitus zones',
 *     documentationURL: '/docs/cards/styx-zone-creator',
 *   });
 */

export interface CustomCardRegistration {
  type: string;
  name: string;
  description?: string;
  documentationURL?: string;
  icon?: string;
  preview?: boolean;
  default?: unknown;
}

declare global {
  interface Window {
    customCards?: CustomCardRegistration[];
  }
}

/**
 * Register a custom card with window.customCards array.
 * Ensures documentationURL is always set (defaults to internal docs).
 *
 * @param card - Card registration metadata
 */
export function registerCustomCard(card: CustomCardRegistration): void {
  // Ensure documentationURL is set
  if (!card.documentationURL) {
    // Default to internal docs path based on card type
    card.documentationURL = `/docs/cards/${card.type.replace(/-card$/, '')}`;
  }

  // Validate documentationURL format
  if (!card.documentationURL.startsWith('http') && !card.documentationURL.startsWith('/')) {
    console.warn(`[PS-174] Invalid documentationURL for ${card.type}: ${card.documentationURL}`);
    card.documentationURL = `/docs/cards/${card.type}`;
  }

  // Register with window.customCards
  if (!window.customCards) {
    window.customCards = [];
  }

  const customCards = window.customCards;
  const existing = customCards.find((registeredCard) => registeredCard.type === card.type);
  if (existing) {
    // Update existing registration
    Object.assign(existing, card);
    console.log(`[PS-174] Updated card registration: ${card.type}`);
  } else {
    // Add new registration
    customCards.push(card);
    console.log(`[PS-174] Registered card: ${card.type} → ${card.documentationURL}`);
  }
}

/**
 * Bulk register multiple cards.
 *
 * @param cards - Array of card registrations
 */
export function registerCustomCards(cards: CustomCardRegistration[]): void {
  cards.forEach(card => registerCustomCard(card));
}

/**
 * Get documentation URL for a card type.
 *
 * @param type - Card type identifier
 * @returns Documentation URL or undefined if not found
 */
export function getCardDocumentationURL(type: string): string | undefined {
  const card = window.customCards?.find((registeredCard) => registeredCard.type === type);
  return card?.documentationURL;
}

/**
 * Validate all registered cards have documentationURL.
 *
 * @returns Array of card types missing documentationURL
 */
export function validateCardDocumentation(): string[] {
  const missing: string[] = [];
  
  window.customCards?.forEach((registeredCard) => {
    if (!registeredCard.documentationURL) {
      missing.push(registeredCard.type);
    }
  });
  
  if (missing.length > 0) {
    console.warn(`[PS-174] ${missing.length} cards missing documentationURL:`, missing);
  }
  
  return missing;
}

// Auto-validate on module load
if (typeof window !== 'undefined' && window.customCards) {
  validateCardDocumentation();
}
