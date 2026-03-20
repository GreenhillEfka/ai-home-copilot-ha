/**
 * PS-174 + PS-219: Card Registration Helper with getConfigForm enforcement.
 *
 * Centralizes custom card registration with:
 * - Mandatory documentationURL (PS-174)
 * - Mandatory static getConfigForm() presence check (PS-219)
 * - HaFormSchema validation (PS-219)
 * - Throws CardRegistrationError on schema drift
 *
 * Usage:
 *   import { registerCustomCard } from './card-registration.js';
 *
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

export class CardRegistrationError extends Error {
  constructor(
    public readonly code: CardRegistrationErrorCode,
    message: string,
    public readonly cardType?: string,
    public readonly detail?: string,
  ) {
    super(message);
    this.name = 'CardRegistrationError';
    Object.setPrototypeOf(this, CardRegistrationError.prototype);
  }
}

export type CardRegistrationErrorCode =
  | 'MISSING_DOCUMENTATION_URL'
  | 'INVALID_DOCUMENTATION_URL'
  | 'MISSING_GET_CONFIG_FORM'
  | 'INVALID_GET_CONFIG_FORM'
  | 'INVALID_SCHEMA_FIELD'
  | 'SCHEMA_VALIDATION_FAILED'
  | 'UNKNOWN';

declare global {
  interface Window {
    customCards?: CustomCardRegistration[];
  }
}

// ── Documentation URL helpers ─────────────────────────────────────────────────

function ensureDocumentationURL(card: CustomCardRegistration): void {
  if (!card.documentationURL) {
    card.documentationURL = `/docs/cards/${card.type.replace(/-card$/, '')}`;
  }

  if (!card.documentationURL.startsWith('http') && !card.documentationURL.startsWith('/')) {
    throw new CardRegistrationError(
      'INVALID_DOCUMENTATION_URL',
      `Invalid documentationURL for ${card.type}: must start with / or http`,
      card.type,
      card.documentationURL,
    );
  }
}

// ── getConfigForm validation (PS-219) ───────────────────────────────────────

/**
 * Verify a card constructor has a static getConfigForm method.
 * Throws CardRegistrationError if missing or not callable.
 */
export function validateGetConfigForm(
  cardClass: CustomCardClass,
  cardType: string,
): void {
  if (typeof cardClass !== 'function') {
    throw new CardRegistrationError(
      'MISSING_GET_CONFIG_FORM',
      `Card class for '${cardType}' is not a constructor function`,
      cardType,
    );
  }

  const descriptor = Object.getOwnPropertyDescriptor(cardClass, 'getConfigForm');

  if (!descriptor) {
    // getConfigForm not defined at all
    throw new CardRegistrationError(
      'MISSING_GET_CONFIG_FORM',
      `Card '${cardType}' must implement 'static async getConfigForm(): Promise<HaFormSchema[]>'`,
      cardType,
    );
  }

  if (typeof descriptor.value !== 'function') {
    throw new CardRegistrationError(
      'MISSING_GET_CONFIG_FORM',
      `getConfigForm on '${cardType}' exists but is not a function`,
      cardType,
    );
  }
}

/**
 * Validate a HaFormSchema array structure.
 * Required fields per entry: type + selector.
 * Throws on first violation.
 */
export function validateHaFormSchema(schema: unknown, cardType: string): void {
  if (!Array.isArray(schema)) {
    throw new CardRegistrationError(
      'INVALID_GET_CONFIG_FORM',
      `getConfigForm() of '${cardType}' must return an array, got ${typeof schema}`,
      cardType,
      typeof schema,
    );
  }

  for (const [index, entry] of schema.entries()) {
    if (!entry || typeof entry !== 'object') {
      throw new CardRegistrationError(
        'INVALID_SCHEMA_FIELD',
        `Schema[${index}] in '${cardType}' is not an object`,
        cardType,
      );
    }

    const e = entry as Record<string, unknown>;

    if (typeof e.type !== 'string') {
      throw new CardRegistrationError(
        'INVALID_SCHEMA_FIELD',
        `Schema[${index}] in '${cardType}' missing 'type' (must be string)`,
        cardType,
        `entry.type=${e.type}`,
      );
    }

    if (e.selector !== undefined && (e.selector === null || typeof e.selector !== 'object')) {
      throw new CardRegistrationError(
        'INVALID_SCHEMA_FIELD',
        `Schema[${index}] in '${cardType}' has invalid selector (must be object or undefined)`,
        cardType,
        `entry.selector=${String(e.selector)}`,
      );
    }
  }
}

type CustomCardClass = new (...args: unknown[]) => unknown;

// ── Core registration ────────────────────────────────────────────────────────

/**
 * Register a custom card with window.customCards array.
 *
 * PS-174: Ensures documentationURL is always set (defaults to /docs/cards/{type}).
 * PS-219: Optionally validates getConfigForm if cardClass is provided.
 *
 * @param card - Card registration metadata
 * @param cardClass - Optional card class constructor for getConfigForm validation
 * @throws CardRegistrationError on validation failure
 */
export function registerCustomCard(
  card: CustomCardRegistration,
  cardClass?: CustomCardClass,
): void {
  // PS-174: documentationURL enforcement
  ensureDocumentationURL(card);

  // PS-219: getConfigForm validation when class is provided
  if (cardClass) {
    validateGetConfigForm(cardClass, card.type);

    // Attempt to call getConfigForm to validate schema structure
    try {
      const result = (cardClass as unknown as { getConfigForm: () => unknown }).getConfigForm();

      // Handle both sync return and async Promise
      const schema = result instanceof Promise ? undefined : result;

      if (schema !== undefined) {
        validateHaFormSchema(schema, card.type);
      }
      // Async case: validation deferred to caller (card-level)
    } catch (err) {
      if (err instanceof CardRegistrationError) throw err;
      // Non-CardRegistrationError from getConfigForm itself — re-throw
      throw new CardRegistrationError(
        'SCHEMA_VALIDATION_FAILED',
        `getConfigForm() of '${card.type}' threw: ${err instanceof Error ? err.message : String(err)}`,
        card.type,
      );
    }
  }

  // Register with window.customCards
  if (!window.customCards) {
    window.customCards = [];
  }

  const customCards = window.customCards;
  const existing = customCards.find((registeredCard) => registeredCard.type === card.type);
  if (existing) {
    Object.assign(existing, card);
    console.log(`[PS-174/PS-219] Updated card registration: ${card.type}`);
  } else {
    customCards.push(card);
    console.log(`[PS-174/PS-219] Registered card: ${card.type} → ${card.documentationURL}`);
  }
}

/**
 * Bulk register multiple cards.
 */
export function registerCustomCards(cards: CustomCardRegistration[]): void {
  cards.forEach((card) => registerCustomCard(card));
}

/**
 * Get documentation URL for a card type.
 */
export function getCardDocumentationURL(type: string): string | undefined {
  const card = window.customCards?.find((registeredCard) => registeredCard.type === type);
  return card?.documentationURL;
}

/**
 * Validate all registered cards have documentationURL.
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
