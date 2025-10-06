/**
 * SecurityUI - Security Indicator and Tooltip Management
 * Handles security indicators and moderation result tooltips
 */
class SecurityUI {
    /**
     * Add security indicator to message
     * @param {HTMLElement} messageElement - Message element
     * @param {Object} moderationResult - Moderation result
     */
    static addIndicator(messageElement, moderationResult) {
        if (!moderationResult) return;

        const openaiResult = moderationResult.openai_result || {};
        const llamaResult = moderationResult.llama_result || {};

        // Determine if there's a security issue
        const hasIssue = openaiResult.flagged || llamaResult.detected_attack;

        // Create indicator element
        const indicator = document.createElement('div');
        indicator.className = `security-indicator ${hasIssue ? 'warning' : 'safe'}`;

        // Store moderation data
        indicator.dataset.moderation = JSON.stringify(moderationResult);

        // Add tooltip on hover
        indicator.addEventListener('mouseenter', (e) => {
            SecurityUI.showTooltip(e.target, moderationResult);
        });

        indicator.addEventListener('mouseleave', () => {
            SecurityUI.hideTooltip();
        });

        // Add to message bubble
        const messageBubble = messageElement.querySelector('.message-bubble');
        if (messageBubble) {
            messageBubble.style.position = 'relative';
            messageBubble.appendChild(indicator);
        }
    }

    /**
     * Show security tooltip
     * @param {HTMLElement} indicatorElement - Security indicator element
     * @param {Object} moderationResult - Moderation result
     */
    static showTooltip(indicatorElement, moderationResult) {
        SecurityUI.hideTooltip(); // Remove any existing tooltip

        const tooltip = document.createElement('div');
        tooltip.className = 'security-tooltip';
        tooltip.id = 'security-tooltip';

        const openaiResult = moderationResult.openai_result || {};
        const llamaResult = moderationResult.llama_result || {};
        const hasIssues = openaiResult.flagged || llamaResult.detected_attack;

        let content = '<div class="tooltip-title">Security Check Results</div>';

        if (hasIssues) {
            // Show OpenAI result if flagged
            if (openaiResult.flagged) {
                content += '<div class="tooltip-section">';
                content += '<div class="tooltip-service">🛡️ OpenAI Moderation</div>';
                content += '<div class="tooltip-status-flagged">Status: Flagged</div>';
                if (openaiResult.top_category) {
                    content += `<div class="tooltip-detail">Category: ${openaiResult.top_category}</div>`;
                }
                if (openaiResult.top_score) {
                    content += `<div class="tooltip-detail">Score: ${openaiResult.top_score.toFixed(3)}</div>`;
                }
                content += '</div>';
            }

            // Show Llama result if detected
            if (llamaResult.detected_attack) {
                content += '<div class="tooltip-section">';
                content += '<div class="tooltip-service">⚠️ Llama Guard</div>';
                content += '<div class="tooltip-status-injection">Status: Injection Detected</div>';
                if (llamaResult.score !== undefined) {
                    content += `<div class="tooltip-detail">Score: ${llamaResult.score.toFixed(3)}</div>`;
                }
                content += '</div>';
            }
        } else {
            content += '<div class="tooltip-all-clear">✅ No issues detected</div>';
        }

        tooltip.innerHTML = content;
        document.body.appendChild(tooltip);

        // Position tooltip
        const rect = indicatorElement.getBoundingClientRect();
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
        tooltip.style.left = (rect.left - tooltip.offsetWidth + 20) + 'px';

        // Ensure tooltip stays in viewport
        const tooltipRect = tooltip.getBoundingClientRect();
        if (tooltipRect.left < 10) {
            tooltip.style.left = '10px';
        }
        if (tooltipRect.top < 10) {
            tooltip.style.top = (rect.bottom + 10) + 'px';
        }
    }

    /**
     * Hide security tooltip
     */
    static hideTooltip() {
        const tooltip = document.getElementById('security-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }
}