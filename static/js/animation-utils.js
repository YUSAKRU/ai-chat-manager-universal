/**
 * 🎬 AI ORCHESTRATOR ANIMATION UTILITIES v2.0
 * Modern micro-interactions and smooth animations
 */

class AnimationUtils {
  constructor() {
    this.init();
  }

  init() {
    this.setupIntersectionObserver();
    this.setupHoverEffects();
    this.setupLoadingStates();
    this.bindEvents();
  }

  /**
   * Setup entrance animations with Intersection Observer
   */
  setupIntersectionObserver() {
    if (!window.IntersectionObserver) return;

    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -10% 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.animateIn(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // Observe elements with animation classes
    document.querySelectorAll('[data-animate]').forEach(el => {
      observer.observe(el);
    });
  }

  /**
   * Animate element entrance
   */
  animateIn(element) {
    const animationType = element.dataset.animate || 'fadeInUp';
    const delay = element.dataset.delay || 0;

    setTimeout(() => {
      element.classList.add('animate-in', `animate-${animationType}`);
    }, delay);
  }

  /**
   * Setup hover micro-interactions
   */
  setupHoverEffects() {
    // Add hover effects to cards
    document.querySelectorAll('.card-modern, .specialist-card').forEach(card => {
      card.addEventListener('mouseenter', (e) => {
        this.addHoverGlow(e.target);
      });

      card.addEventListener('mouseleave', (e) => {
        this.removeHoverGlow(e.target);
      });
    });

    // Add click ripple effect to buttons
    document.querySelectorAll('.btn-modern').forEach(button => {
      button.addEventListener('click', (e) => {
        this.createRippleEffect(e);
      });
    });
  }

  /**
   * Add glow effect on hover
   */
  addHoverGlow(element) {
    element.style.transition = 'all 0.3s ease';
    element.style.boxShadow = '0 20px 40px rgba(0,0,0,0.15), 0 0 20px rgba(59, 130, 246, 0.1)';
  }

  /**
   * Remove glow effect
   */
  removeHoverGlow(element) {
    element.style.boxShadow = '';
  }

  /**
   * Create ripple effect on button click
   */
  createRippleEffect(event) {
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    // Remove existing ripples
    button.querySelectorAll('.ripple').forEach(ripple => ripple.remove());

    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.cssText = `
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.6);
      transform: scale(0);
      animation: ripple-animation 0.6s ease-out;
      left: ${x}px;
      top: ${y}px;
      width: ${size}px;
      height: ${size}px;
      pointer-events: none;
    `;

    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);

    // Clean up after animation
    setTimeout(() => {
      ripple.remove();
    }, 600);
  }

  /**
   * Setup loading states
   */
  setupLoadingStates() {
    // Add loading animations CSS if not exists
    this.addLoadingStyles();
  }

  /**
   * Add loading animation styles
   */
  addLoadingStyles() {
    if (document.querySelector('#animation-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'animation-styles';
    styles.innerHTML = `
      /* Ripple Effect */
      @keyframes ripple-animation {
        to {
          transform: scale(4);
          opacity: 0;
        }
      }

      /* Entrance Animations */
      [data-animate] {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.6s ease;
      }

      .animate-in {
        opacity: 1 !important;
        transform: translateY(0) !important;
      }

      .animate-fadeInUp {
        transform: translateY(30px);
      }

      .animate-fadeInLeft {
        transform: translateX(-30px);
      }

      .animate-fadeInRight {
        transform: translateX(30px);
      }

      .animate-fadeInScale {
        transform: scale(0.9);
      }

      /* Loading Pulse */
      .loading-pulse {
        animation: pulse 2s ease-in-out infinite;
      }

      @keyframes pulse {
        0%, 100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }

      /* Skeleton Loading */
      .skeleton {
        background: linear-gradient(90deg, 
          var(--bg-tertiary) 25%, 
          var(--bg-secondary) 50%, 
          var(--bg-tertiary) 75%);
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s infinite;
      }

      @keyframes skeleton-loading {
        0% {
          background-position: 200% 0;
        }
        100% {
          background-position: -200% 0;
        }
      }

      /* Floating Animation */
      .floating {
        animation: floating 3s ease-in-out infinite;
      }

      @keyframes floating {
        0%, 100% {
          transform: translateY(0px);
        }
        50% {
          transform: translateY(-10px);
        }
      }

      /* Bounce In */
      .bounce-in {
        animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      }

      @keyframes bounceIn {
        0% {
          transform: scale(0.3);
          opacity: 0;
        }
        50% {
          transform: scale(1.05);
        }
        70% {
          transform: scale(0.9);
        }
        100% {
          transform: scale(1);
          opacity: 1;
        }
      }

      /* Slide In Animations */
      .slide-in-top {
        animation: slideInTop 0.5s ease-out;
      }

      @keyframes slideInTop {
        from {
          transform: translateY(-100%);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }

      .slide-in-bottom {
        animation: slideInBottom 0.5s ease-out;
      }

      @keyframes slideInBottom {
        from {
          transform: translateY(100%);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }

      /* Stagger Animation Delays */
      .stagger-1 { animation-delay: 0.1s; }
      .stagger-2 { animation-delay: 0.2s; }
      .stagger-3 { animation-delay: 0.3s; }
      .stagger-4 { animation-delay: 0.4s; }
      .stagger-5 { animation-delay: 0.5s; }

      /* Typing Animation */
      .typing-cursor::after {
        content: '|';
        animation: blink 1s infinite;
      }

      @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
      }

      /* Smooth Transitions */
      .smooth-transition {
        transition: all 0.3s ease;
      }

      /* Reduce motion for accessibility */
      @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
      }
    `;

    document.head.appendChild(styles);
  }

  /**
   * Animate message appearance
   */
  animateMessage(messageElement, type = 'user') {
    messageElement.style.opacity = '0';
    messageElement.style.transform = type === 'user' 
      ? 'translateX(20px)' 
      : 'translateX(-20px)';

    requestAnimationFrame(() => {
      messageElement.style.transition = 'all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
      messageElement.style.opacity = '1';
      messageElement.style.transform = 'translateX(0)';
    });
  }

  /**
   * Typing animation for text
   */
  typeText(element, text, speed = 50) {
    return new Promise((resolve) => {
      element.textContent = '';
      element.classList.add('typing-cursor');
      
      let i = 0;
      const timer = setInterval(() => {
        element.textContent += text.charAt(i);
        i++;
        
        if (i >= text.length) {
          clearInterval(timer);
          element.classList.remove('typing-cursor');
          resolve();
        }
      }, speed);
    });
  }

  /**
   * Number counting animation
   */
  countUp(element, start, end, duration = 1000) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
      current += increment;
      
      if (current >= end) {
        current = end;
        clearInterval(timer);
      }
      
      element.textContent = Math.floor(current);
    }, 16);
  }

  /**
   * Show skeleton loading
   */
  showSkeleton(container, lines = 3) {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-container';
    
    for (let i = 0; i < lines; i++) {
      const line = document.createElement('div');
      line.className = 'skeleton';
      line.style.cssText = `
        height: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0.25rem;
        width: ${90 - (i * 10)}%;
      `;
      skeleton.appendChild(line);
    }
    
    container.innerHTML = '';
    container.appendChild(skeleton);
  }

  /**
   * Hide skeleton and show content
   */
  hideSkeleton(container, content) {
    container.innerHTML = content;
  }

  /**
   * Animate progress bar
   */
  animateProgress(progressBar, percentage, duration = 1000) {
    let current = 0;
    const increment = percentage / (duration / 16);

    const timer = setInterval(() => {
      current += increment;
      
      if (current >= percentage) {
        current = percentage;
        clearInterval(timer);
      }
      
      progressBar.style.width = `${current}%`;
    }, 16);
  }

  /**
   * Stagger animations for multiple elements
   */
  staggerAnimation(elements, animationClass, delay = 100) {
    elements.forEach((element, index) => {
      setTimeout(() => {
        element.classList.add(animationClass);
      }, index * delay);
    });
  }

  /**
   * Parallax effect for elements
   */
  setupParallax() {
    const parallaxElements = document.querySelectorAll('[data-parallax]');
    
    if (parallaxElements.length === 0) return;

    const handleScroll = () => {
      const scrolled = window.pageYOffset;
      
      parallaxElements.forEach(element => {
        const rate = scrolled * -0.5;
        element.style.transform = `translateY(${rate}px)`;
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
  }

  /**
   * Bind global animation events
   */
  bindEvents() {
    // Auto-add animation attributes to new elements
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) { // Element node
            // Add entrance animation to cards
            if (node.classList?.contains('card-modern') || 
                node.classList?.contains('specialist-card')) {
              node.setAttribute('data-animate', 'fadeInUp');
              if (window.IntersectionObserver) {
                this.setupIntersectionObserver();
              }
            }
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Add scroll-triggered animations
    this.setupParallax();
  }

  /**
   * Quick pulse effect for notifications
   */
  pulse(element, intensity = 1.1) {
    element.style.transition = 'transform 0.2s ease';
    element.style.transform = `scale(${intensity})`;
    
    setTimeout(() => {
      element.style.transform = 'scale(1)';
    }, 200);
  }

  /**
   * Shake animation for errors
   */
  shake(element) {
    element.style.animation = 'shake 0.5s ease';
    setTimeout(() => {
      element.style.animation = '';
    }, 500);
  }
}

// Add shake keyframes if not exists
if (!document.querySelector('#shake-animation')) {
  const shakeStyles = document.createElement('style');
  shakeStyles.id = 'shake-animation';
  shakeStyles.innerHTML = `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-5px); }
      75% { transform: translateX(5px); }
    }
  `;
  document.head.appendChild(shakeStyles);
}

// Auto-initialize animation utils
let animationUtils;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    animationUtils = new AnimationUtils();
  });
} else {
  animationUtils = new AnimationUtils();
}

// Export for global access
window.animationUtils = animationUtils;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AnimationUtils;
} 