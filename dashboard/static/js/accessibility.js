/**
 * PilotSuite Styx Dashboard — Accessibility Enhancements
 * WCAG 2.1 AA Compliance — Keyboard Navigation & Screen Reader Support
 * 
 * This script provides accessibility improvements including:
 * - Enhanced keyboard navigation
 * - Screen reader announcements
 * - ARIA attribute management
 * - Focus management
 * 
 * Usage: Include after dashboard.js
 * <script src="accessibility.js"></script>
 */

(function() {
  'use strict';

  // ==========================================================================
  // Accessibility Manager Class
  // ==========================================================================
  
  class AccessibilityManager {
    constructor() {
      this.announcementQueue = [];
      this.isAnnouncing = false;
      this.preferredMotion = this.getMotionPreference();
      this.init();
    }

    // --------------------------------------------------------------------------
    // Initialization
    // --------------------------------------------------------------------------
    
    init() {
      console.log('[A11Y] Accessibility Manager initialized');
      
      // Wait for DOM to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.setup());
      } else {
        this.setup();
      }
    }

    setup() {
      this.addSkipLink();
      this.addLandmarkRoles();
      this.setupTabNavigation();
      this.setupZoneCards();
      this.setupChatWidget();
      this.setupScrollButtons();
      this.setupThemeToggle();
      this.setupLiveRegions();
      this.setupKeyboardShortcuts();
      this.applyReducedMotion();
      
      console.log('[A11Y] Accessibility features activated');
    }

    // --------------------------------------------------------------------------
    // Motion Preference Detection
    // --------------------------------------------------------------------------
    
    getMotionPreference() {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    applyReducedMotion() {
      if (this.preferredMotion) {
        document.documentElement.style.setProperty('--motion-duration', '0.01ms');
        console.log('[A11Y] Reduced motion preference detected');
      }
    }

    // --------------------------------------------------------------------------
    // Skip Link — WCAG 2.4.1 Bypass Blocks
    // --------------------------------------------------------------------------
    
    addSkipLink() {
      // Check if skip link already exists
      if (document.querySelector('.skip-link')) {
        return;
      }

      const skipLink = document.createElement('a');
      skipLink.href = '#main-content';
      skipLink.className = 'skip-link';
      skipLink.textContent = 'Zum Hauptinhalt springen';
      
      // Add at the beginning of body
      const body = document.body;
      if (body.firstChild) {
        body.insertBefore(skipLink, body.firstChild);
      } else {
        body.appendChild(skipLink);
      }

      console.log('[A11Y] Skip link added');
    }

    // --------------------------------------------------------------------------
    // Landmark Roles — WCAG 2.4.1 Bypass Blocks
    // --------------------------------------------------------------------------
    
    addLandmarkRoles() {
      // Add landmark roles if not present
      const header = document.querySelector('header');
      if (header && !header.getAttribute('role')) {
        header.setAttribute('role', 'banner');
      }

      const nav = document.querySelector('nav');
      if (nav && !nav.getAttribute('role')) {
        nav.setAttribute('role', 'navigation');
        nav.setAttribute('aria-label', 'Hauptmenü');
      }

      const main = document.querySelector('main');
      if (main && !main.getAttribute('role')) {
        main.setAttribute('role', 'main');
        main.setAttribute('id', 'main-content');
      }

      const footer = document.querySelector('footer');
      if (footer && !footer.getAttribute('role')) {
        footer.setAttribute('role', 'contentinfo');
      }

      console.log('[A11Y] Landmark roles added');
    }

    // --------------------------------------------------------------------------
    // Tab Navigation Accessibility — WCAG 4.1.2 Name, Role, Value
    // --------------------------------------------------------------------------
    
    setupTabNavigation() {
      const tabList = document.querySelector('.tabs-container');
      if (!tabList) {
        console.warn('[A11Y] Tab container not found');
        return;
      }

      // Add tablist role
      tabList.setAttribute('role', 'tablist');
      tabList.setAttribute('aria-label', 'Habituszonen');

      // Get all tab buttons
      const tabs = tabList.querySelectorAll('.tab-item');
      
      tabs.forEach((tab, index) => {
        // Add tab role
        tab.setAttribute('role', 'tab');
        
        // Get zone ID from data attribute
        const zoneId = tab.dataset.zone;
        const pane = document.getElementById(`pane-${zoneId}`);
        
        // Set ARIA attributes
        tab.setAttribute('aria-controls', `pane-${zoneId}`);
        tab.setAttribute('id', `tab-${zoneId}`);
        
        // Set initial aria-selected
        const isSelected = tab.classList.contains('active');
        tab.setAttribute('aria-selected', isSelected ? 'true' : 'false');
        
        // Set tabindex
        tab.setAttribute('tabindex', isSelected ? '0' : '-1');
        
        // Add keyboard navigation
        tab.addEventListener('keydown', (e) => this.handleTabKeydown(e, tabs, index));
        
        // Set up panel
        if (pane) {
          pane.setAttribute('role', 'tabpanel');
          pane.setAttribute('aria-labelledby', `tab-${zoneId}`);
          pane.setAttribute('tabindex', '0');
          
          if (!isSelected) {
            pane.setAttribute('aria-hidden', 'true');
          }
        }
      });

      console.log('[A11Y] Tab navigation accessibility enabled');
    }

    handleTabKeydown(event, tabs, currentIndex) {
      let newIndex = currentIndex;
      let handled = false;

      switch (event.key) {
        case 'ArrowLeft':
          newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
          handled = true;
          break;
          
        case 'ArrowRight':
          newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
          handled = true;
          break;
          
        case 'Home':
          newIndex = 0;
          handled = true;
          break;
          
        case 'End':
          newIndex = tabs.length - 1;
          handled = true;
          break;
          
        case 'Enter':
        case ' ':
          // Activate current tab
          tabs[currentIndex].click();
          handled = true;
          break;
      }

      if (handled) {
        event.preventDefault();
        
        if (newIndex !== currentIndex) {
          this.switchTab(tabs[newIndex]);
        }
      }
    }

    switchTab(newTab) {
      if (!newTab) return;

      const zoneId = newTab.dataset.zone;
      
      // Call existing dashboard switchTab if available
      if (window.dashboard && typeof window.dashboard.switchTab === 'function') {
        window.dashboard.switchTab(zoneId);
      }

      // Announce to screen readers
      const tabText = newTab.textContent.trim();
      this.announce(`Zu ${tabText} gewechselt`);
    }

    // --------------------------------------------------------------------------
    // Zone Cards Accessibility — WCAG 2.1.1 Keyboard
    // --------------------------------------------------------------------------
    
    setupZoneCards() {
      // Use MutationObserver to handle dynamically created zone cards
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.classList && node.classList.contains('zone-card')) {
              this.makeZoneCardAccessible(node);
            }
          });
        });
      });

      // Start observing
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      // Handle existing zone cards
      document.querySelectorAll('.zone-card').forEach((card) => {
        this.makeZoneCardAccessible(card);
      });

      console.log('[A11Y] Zone cards accessibility enabled');
    }

    makeZoneCardAccessible(card) {
      // Skip if already processed
      if (card.getAttribute('data-a11y-processed')) {
        return;
      }

      // Make focusable
      card.setAttribute('tabindex', '0');
      card.setAttribute('role', 'button');
      
      // Add keyboard support
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          card.click();
        }
      });

      // Add accessible name if not present
      if (!card.getAttribute('aria-label')) {
        const title = card.querySelector('.zone-card-title');
        if (title) {
          card.setAttribute('aria-label', title.textContent.trim());
        }
      }

      // Mark as processed
      card.setAttribute('data-a11y-processed', 'true');
    }

    // --------------------------------------------------------------------------
    // Chat Widget Accessibility — WCAG 4.1.3 Status Messages
    // --------------------------------------------------------------------------
    
    setupChatWidget() {
      const chatMessages = document.getElementById('chat-messages');
      const chatInput = document.getElementById('chat-input');
      const sendButton = document.getElementById('btn-send');
      const typingIndicator = document.getElementById('typing-indicator');
      const messageCount = document.getElementById('message-count');

      if (chatMessages) {
        // Add role="log" for chat messages
        chatMessages.setAttribute('role', 'log');
        chatMessages.setAttribute('aria-live', 'polite');
        chatMessages.setAttribute('aria-label', 'Chat-Nachrichten');
      }

      if (chatInput) {
        // Add label
        const label = document.createElement('label');
        label.setAttribute('for', 'chat-input');
        label.className = 'sr-only';
        label.textContent = 'Nachricht eingeben';
        chatInput.parentNode.insertBefore(label, chatInput);

        // Add character counter
        const counter = document.createElement('span');
        counter.id = 'char-counter';
        counter.className = 'sr-only';
        counter.setAttribute('aria-live', 'polite');
        counter.textContent = '0 von 2000 Zeichen';
        chatInput.parentNode.appendChild(counter);

        // Update counter on input
        chatInput.addEventListener('input', () => {
          const count = chatInput.value.length;
          counter.textContent = `${count} von ${chatInput.maxLength} Zeichen`;
        });
      }

      if (sendButton) {
        // Ensure button has accessible name
        if (!sendButton.getAttribute('aria-label')) {
          sendButton.setAttribute('aria-label', 'Nachricht senden');
        }
      }

      if (typingIndicator) {
        typingIndicator.setAttribute('aria-live', 'polite');
        typingIndicator.setAttribute('aria-label', 'Schreibt...');
      }

      if (messageCount) {
        messageCount.setAttribute('aria-live', 'polite');
      }

      console.log('[A11Y] Chat widget accessibility enabled');
    }

    // --------------------------------------------------------------------------
    // Scroll Buttons Accessibility
    // --------------------------------------------------------------------------
    
    setupScrollButtons() {
      const scrollLeft = document.getElementById('scroll-left');
      const scrollRight = document.getElementById('scroll-right');

      if (scrollLeft) {
        if (!scrollLeft.getAttribute('aria-label')) {
          scrollLeft.setAttribute('aria-label', 'Nach links scrollen');
        }
      }

      if (scrollRight) {
        if (!scrollRight.getAttribute('aria-label')) {
          scrollRight.setAttribute('aria-label', 'Nach rechts scrollen');
        }
      }

      console.log('[A11Y] Scroll buttons accessibility enabled');
    }

    // --------------------------------------------------------------------------
    // Theme Toggle Accessibility
    // --------------------------------------------------------------------------
    
    setupThemeToggle() {
      const themeToggle = document.getElementById('theme-toggle');
      
      if (themeToggle) {
        // Add accessible name
        themeToggle.setAttribute('aria-label', 'Theme umschalten');
        themeToggle.setAttribute('role', 'button');
        themeToggle.setAttribute('tabindex', '0');

        // Add keyboard support
        themeToggle.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            themeToggle.click();
          }
        });

        // Announce theme change
        const originalClick = themeToggle.onclick;
        themeToggle.onclick = () => {
          if (originalClick) originalClick.call(themeToggle);
          
          setTimeout(() => {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            this.announce(`Theme geändert zu ${isDark ? 'Dunkel' : 'Hell'}`);
          }, 100);
        };
      }

      console.log('[A11Y] Theme toggle accessibility enabled');
    }

    // --------------------------------------------------------------------------
    // Live Regions — WCAG 4.1.3 Status Messages
    // --------------------------------------------------------------------------
    
    setupLiveRegions() {
      // Create announcement container
      const announcer = document.createElement('div');
      announcer.id = 'a11y-announcer';
      announcer.className = 'sr-only';
      announcer.setAttribute('aria-live', 'polite');
      announcer.setAttribute('aria-atomic', 'true');
      document.body.appendChild(announcer);

      // Create alert container for important messages
      const alertAnnouncer = document.createElement('div');
      alertAnnouncer.id = 'a11y-alerts';
      alertAnnouncer.className = 'sr-only';
      alertAnnouncer.setAttribute('aria-live', 'assertive');
      alertAnnouncer.setAttribute('aria-atomic', 'true');
      document.body.appendChild(alertAnnouncer);

      // Enhance connection status
      const connectionStatus = document.getElementById('connection-status');
      if (connectionStatus) {
        connectionStatus.setAttribute('role', 'status');
        connectionStatus.setAttribute('aria-live', 'polite');
      }

      // Enhance alert badge
      const alertBadge = document.getElementById('alert-badge');
      if (alertBadge) {
        const parent = alertBadge.closest('.active-alerts');
        if (parent) {
          parent.setAttribute('aria-live', 'polite');
          parent.setAttribute('aria-label', 'Aktive Warnungen');
        }
      }

      console.log('[A11Y] Live regions configured');
    }

    // --------------------------------------------------------------------------
    // Screen Reader Announcements
    // --------------------------------------------------------------------------
    
    announce(message, priority = 'polite') {
      const announcerId = priority === 'assertive' ? 'a11y-alerts' : 'a11y-announcer';
      const announcer = document.getElementById(announcerId);
      
      if (!announcer) {
        console.warn('[A11Y] Announcer not found');
        return;
      }

      // Clear previous announcement
      announcer.textContent = '';

      // Queue announcement
      this.announcementQueue.push(message);
      this.processAnnouncementQueue();
    }

    processAnnouncementQueue() {
      if (this.isAnnouncing || this.announcementQueue.length === 0) {
        return;
      }

      this.isAnnouncing = true;
      const message = this.announcementQueue.shift();
      const announcer = document.getElementById('a11y-announcer');

      if (announcer) {
        // Small delay to ensure screen reader picks up the change
        setTimeout(() => {
          announcer.textContent = message;
          
          // Clear after announcement
          setTimeout(() => {
            announcer.textContent = '';
            this.isAnnouncing = false;
            this.processAnnouncementQueue();
          }, 1000);
        }, 100);
      }
    }

    // --------------------------------------------------------------------------
    // Keyboard Shortcuts — WCAG 2.1.1 Keyboard
    // --------------------------------------------------------------------------
    
    setupKeyboardShortcuts() {
      document.addEventListener('keydown', (e) => {
        // Alt + 1-9: Quick navigation to zones
        if (e.altKey && e.key >= '1' && e.key <= '9') {
          e.preventDefault();
          const zoneIndex = parseInt(e.key) - 1;
          const tabs = document.querySelectorAll('.tab-item');
          
          if (tabs[zoneIndex]) {
            this.switchTab(tabs[zoneIndex]);
          }
        }

        // Alt + H: Go to home (first tab)
        if (e.altKey && (e.key === 'h' || e.key === 'H')) {
          e.preventDefault();
          const tabs = document.querySelectorAll('.tab-item');
          if (tabs.length > 0) {
            this.switchTab(tabs[0]);
          }
        }

        // Escape: Close modals (if any)
        if (e.key === 'Escape') {
          const modal = document.querySelector('.sensor-modal:not(.hidden)');
          if (modal) {
            const closeBtn = modal.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
          }
        }
      });

      console.log('[A11Y] Keyboard shortcuts enabled');
    }

    // --------------------------------------------------------------------------
    // Dynamic Content Updates
    // --------------------------------------------------------------------------
    
    announceUpdate(type, data) {
      switch (type) {
        case 'connection':
          if (data.status === 'connected') {
            this.announce('Mit Server verbunden');
          } else {
            this.announce('Verbindung zum Server getrennt', 'assertive');
          }
          break;

        case 'alert':
          if (data.count > 0) {
            this.announce(`${data.count} neue Warnung${data.count > 1 ? 'en' : ''}`, 'assertive');
          }
          break;

        case 'zone':
          if (data.zoneName) {
            this.announce(`${data.zoneName} aktualisiert`);
          }
          break;

        case 'loading':
          if (data.start) {
            this.announce('Laden gestartet');
          } else {
            this.announce('Laden abgeschlossen');
          }
          break;
      }
    }
  }

  // ==========================================================================
  // Initialize Accessibility Manager
  // ==========================================================================
  
  const a11y = new AccessibilityManager();

  // Make it globally available for integration with existing code
  window.a11y = a11y;

  // ==========================================================================
  // Integration Hooks — Connect with existing dashboard.js
  // ==========================================================================
  
  // Hook into dashboard connection status updates
  if (window.dashboard) {
    const originalUpdateConnectionStatus = window.dashboard.updateConnectionStatus;
    if (originalUpdateConnectionStatus) {
      window.dashboard.updateConnectionStatus = function(status) {
        originalUpdateConnectionStatus.call(this, status);
        a11y.announceUpdate('connection', { status });
      };
    }

    const originalUpdateTotalAlerts = window.dashboard.updateTotalAlerts;
    if (originalUpdateTotalAlerts) {
      window.dashboard.updateTotalAlerts = function() {
        originalUpdateTotalAlerts.call(this);
        const total = this.zones.reduce((sum, z) => sum + z.alertCount, 0);
        a11y.announceUpdate('alert', { count: total });
      };
    }
  }

  console.log('[A11Y] Accessibility integration complete');

})();
