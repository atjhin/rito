// Global state and helper functions
const state = { champions: [], models: [], counter: 0, MAX: 4, MIN: 2, retryCount: 0 };
const escapeHtml = (s) => s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&#39;' }[c]));
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

/**
 * Displays a short-lived message at the bottom of the screen.
 */
function toast(msg) {
    const s = $('#snack');
    if (!s) return;
    s.textContent = msg;
    s.classList.add('show');
    setTimeout(() => s.classList.remove('show'), 3000);
}

/**
 * Loads a list from a text file, with fallbacks.
 */
async function loadList(path) {
    try {
        const res = await fetch(path);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const text = await res.text();
        return text.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    } catch (err) {
        console.warn(`Failed to load ${path}:`, err);
        if (location.protocol === 'file:') {
            toast(`Running from file:// — using fallback data for ${path}`);
        }
        const id = path.includes('champ') ? 'fallbackChampions' : 'fallbackModels';
        const el = document.getElementById(id);
        if (el) {
            try { return JSON.parse(el.textContent).filter(Boolean); } catch (e) { }
        }
        return path.includes('champ')
            ? ["Ahri", "Annie", "Ezreal", "Lulu", "Malzahar", "Twisted Fate", "Vladmir", "Zed"]
            : ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet", "claude-3-opus", "llama-3.1-70b", "mistral-large", "gemini-2.5-flash"];
    }
}

/**
 * Populates a <select> element with <option> tags.
 */
function renderModelOptions(selectEl, models, currentSelected = []) {
    selectEl.innerHTML = models.map(m => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join('');
    [...selectEl.options].forEach(o => {
        if (currentSelected.includes(o.value)) o.selected = true;
    });
}

/**
 * Synchronizes the selected options in the <select> with the visible pills.
 */
function syncPills(selectEl, pillbar, onRemove) {
    const selected = [...selectEl.selectedOptions].map(o => o.value);

    [...pillbar.children].forEach(pill => {
        const value = pill.dataset.value;
        if (!selected.includes(value)) {
            pill.classList.add('removing');
            pill.addEventListener('animationend', () => pill.remove(), { once: true });
        }
    });

    selected.forEach(val => {
        if (![...pillbar.children].some(p => p.dataset.value === val)) {
            const pill = document.createElement('span');
            pill.className = 'pill';
            pill.dataset.value = val;
            pill.innerHTML = `${escapeHtml(val)} <button type="button" title="Remove ${escapeHtml(val)}" aria-label="Remove ${escapeHtml(val)}"><span aria-hidden="true">×</span></button>`;

            const removeBtn = pill.querySelector('button');
            removeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (onRemove) onRemove(val);
            });

            pillbar.appendChild(pill);
        }
    });
}

/**
 * Gets a list of all current character names.
 */
function getNames() {
    return $$('.char-card .char-name-input').map(i => i.value.trim());
}

/**
 * Finds all duplicate names from a list.
 */
function findDuplicateSet(names) {
    const seen = new Set();
    const dupes = new Set();
    names.forEach(n => {
        const key = n.trim().toLowerCase();
        if (!key) return;
        if (seen.has(key)) dupes.add(key);
        else seen.add(key);
    });
    return dupes;
}

/**
 * Refreshes all <datalist> elements to only show available champion names.
 */
function refreshDatalists() {
    const used = new Set(getNames().filter(Boolean).map(n => n.toLowerCase()));
    $$('.char-card').forEach(card => {
        const input = card.querySelector('.char-name-input');
        const datalist = card.querySelector('datalist');
        const current = input.value.trim().toLowerCase();
        const options = state.champions.filter(c => {
            const lc = c.toLowerCase();
            return lc === current || !used.has(lc);
        });
        datalist.innerHTML = options.map(c => `<option value="${escapeHtml(c)}"></option>`).join('');
    });
}

/**
 * Checks if an input's value is a duplicate and clears it if so.
 */
function enforceUniqueName(inputEl) {
    const name = inputEl.value.trim();

    if (!name) {
        refreshDatalists();
        return;
    }

    const inputs = $$('.char-name-input');
    const lower = name.toLowerCase();
    const dup = inputs.some(i => i !== inputEl && i.value.trim().toLowerCase() === lower);

    if (dup) {
        toast('⚠️ Duplicate character name not allowed.');
        inputEl.value = '';
        inputEl.classList.add('invalid');

        // FIX for persistent datalist: defer validation/refresh
        setTimeout(() => {
            refreshDatalists();
            validateForm();
            markValidity();
        }, 10);
        return;
    }

    refreshDatalists();
}

/**
 * Marks all invalid fields in the form with a visual style.
 */
function markValidity() {
    const storyTextarea = $('#story');
    const storyValid = storyTextarea.value.trim().length > 0;
    storyTextarea.classList.toggle('invalid', !storyValid);

    const storyHint = $('#storyHint');
    if (storyHint) {
        storyHint.style.display = storyValid ? 'none' : 'block';
    }

    const cards = $$('.char-card');
    const names = getNames();
    const dupes = findDuplicateSet(names);

    cards.forEach(card => {
        const nameInput = card.querySelector('.char-name-input');
        const name = nameInput.value.trim();
        const duplicate = name && dupes.has(name.toLowerCase());
        const models = [...card.querySelector('select').selectedOptions];

        nameInput.classList.toggle('invalid', !name || duplicate);
        const isValid = name && models.length && !duplicate;
        card.classList.toggle('invalid', !isValid);
    });
}

/**
 * Creates a new character card DOM node from the template.
 */
function createCharacterCard({ name = '', personality = '', preselected = [] } = {}) {
    const tpl = document.getElementById('charCardTemplate');
    const node = tpl.content.cloneNode(true);
    const card = node.querySelector('.char-card');
    const removeBtn = node.querySelector('.remove-btn');

    const nameInput = node.querySelector('.char-name-input');
    const personalityInput = node.querySelector('.char-personality-input');
    const personalityCount = node.querySelector('.char-personality-count');
    const datalist = node.querySelector('datalist');
    const select = node.querySelector('select');
    const pillbar = node.querySelector('.pillbar');
    const modelsLabel = node.querySelector('.multi label');

    const id = `char-${++state.counter}`;
    card.dataset.charId = id;
    nameInput.setAttribute('list', `${id}-champions`);
    datalist.id = `${id}-champions`;
    modelsLabel.setAttribute('for', `${id}-models`);
    select.id = `${id}-models`;

    datalist.innerHTML = state.champions.map(c => `<option value="${escapeHtml(c)}"></option>`).join('');
    nameInput.value = name;

    // Set personality value and update counter
    if (personalityInput) {
        personalityInput.value = personality;
        if (personalityCount) {
            personalityCount.textContent = `${personality.length} / 200`;
        }
    }

    const selectedModels = preselected.length > 0 ? preselected : ['gemini-2.5-flash'];
    renderModelOptions(select, state.models, selectedModels);

    const selectedSet = new Set(selectedModels);

    function updateSelectState() {
        [...select.options].forEach(opt => {
            opt.selected = selectedSet.has(opt.value);
        });
    }

    function toggleOption(optionValue) {
        if (selectedSet.has(optionValue)) {
            selectedSet.delete(optionValue);
        } else {
            selectedSet.add(optionValue);
        }
        updateSelectState();
        syncPills(select, pillbar, toggleOption);
        validateForm();
        markValidity();
    }

    select.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'OPTION') {
            e.preventDefault();
            e.stopPropagation();
            toggleOption(e.target.value);
            return false;
        }
    });

    select.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();
            const focusedOption = select.querySelector('option:focus');
            if (focusedOption) {
                toggleOption(focusedOption.value);
            }
        }
    });

    select.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        return false;
    });

    select.addEventListener('change', e => {
        e.preventDefault();
        e.stopPropagation();
        return false;
    });

    select.addEventListener('mousemove', e => {
        e.preventDefault();
    });

    updateSelectState();
    syncPills(select, pillbar, toggleOption);

    // Personality character counter
    if (personalityInput && personalityCount) {
        personalityInput.addEventListener('input', () => {
            const length = personalityInput.value.length;
            personalityCount.textContent = `${length} / 200`;
            validateForm();
            markValidity();
        });
    }

    nameInput.addEventListener('input', () => {
        validateForm();
        markValidity();
    });

    nameInput.addEventListener('change', () => {
        validateForm();
        markValidity();
    });

    nameInput.addEventListener('blur', () => {
        enforceUniqueName(nameInput);
        validateForm();
        markValidity();
    });

    // 🚀 FIX FOR INSTANT CARD REMOVAL
    removeBtn.addEventListener('click', () => {
        const total = $$('#charCarousel .char-card').length;
        if (total <= state.MIN) {
            toast(`⚠️ At least ${state.MIN} characters are required.`);
            return;
        }

        // Function to handle the removal and subsequent cleanup
        const handleRemoval = () => {
            // Check if the card is still in the DOM before removing
            if (card.parentNode) {
                card.remove();
                applyLayout();
                updateAddButtonState();
                refreshDatalists();
                validateForm();
                markValidity();
            }
        };

        // 🔑 Call the removal logic immediately to bypass animation/timeout delay.
        handleRemoval();
    });

    return node;
}

/**
 * Adjusts card layout based on count.
 */
function applyLayout() {
    const cards = $$('#charCarousel .char-card');
    if (cards.length <= 2) {
        cards.forEach(c => c.style.flex = '0 0 calc(50% - 10px)');
    } else {
        cards.forEach(c => c.style.flex = '0 0 400px');
    }
}

/**
 * Adds a new character card to the carousel.
 */
function addCharacter(defaults = {}, opts = {}) {
    const animate = opts.animate !== false;
    const wrap = $('#charCarousel');
    const count = $$('.char-card', wrap).length;
    if (count >= state.MAX) {
        toast(`⚠️ Maximum of ${state.MAX} characters reached.`);
        return;
    }
    const cardFrag = createCharacterCard(defaults);
    wrap.appendChild(cardFrag);

    const added = wrap.lastElementChild;
    if (animate && added && added.classList.contains('char-card')) {
        added.style.opacity = '0';
        added.style.transform = 'translateY(12px) scale(0.96)';
        setTimeout(() => {
            added.style.transition = 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
            added.style.opacity = '1';
            added.style.transform = 'translateY(0) scale(1)';
        }, 10);
    }

    applyLayout();
    const after = $$('.char-card', wrap).length;
    if (animate && after > 2) {
        setTimeout(() => wrap.scrollTo({ left: wrap.scrollWidth, behavior: 'smooth' }), 100);
    }

    updateAddButtonState();
    refreshDatalists();
    validateForm();
    markValidity();
}

/**
 * Enables or disables the "Add Character" button based on count.
 */
function updateAddButtonState() {
    const addBtn = $('#addCharBtn');
    const count = $$('#charCarousel .char-card').length;
    const disable = count >= state.MAX;
    addBtn.disabled = disable;
    addBtn.title = disable ? `Maximum of ${state.MAX} characters reached` : 'Add character';
    addBtn.setAttribute('aria-disabled', String(disable));
}

/**
 * Validates the entire form and enables/disables the submit button.
 */
function validateForm() {
    const submitBtn = $('#submitBtn');
    const story = $('#story').value.trim();
    const cards = $$('.char-card');

    const okStory = story.length > 0;
    const okCount = cards.length >= state.MIN && cards.length <= state.MAX;

    const names = getNames();
    const dupes = findDuplicateSet(names);
    const okUnique = dupes.size === 0;

    const okEach = cards.every(card => {
        const name = card.querySelector('.char-name-input').value.trim();
        const models = [...card.querySelector('select').selectedOptions].map(o => o.value);
        const duplicate = name && dupes.has(name.toLowerCase());
        return name.length > 0 && models.length > 0 && !duplicate;
    });

    const allValid = okStory && okCount && okEach && okUnique;
    submitBtn.disabled = !allValid;
    return allValid;
}

/**
 * Gathers all form data into a single object.
 */
function buildPayload() {
    const story = $('#story').value.trim();
    const chars = [...$$('.char-card')].map((card) => {
        const name = card.querySelector('.char-name-input').value.trim();
        const personalityInput = card.querySelector('.char-personality-input');
        const personality = personalityInput ? personalityInput.value.trim() : '';
        const models = [...card.querySelector('select').selectedOptions].map(o => o.value);

        return {
            name,
            personality: personality || null,
            models
        };
    });
    return { story, characters: chars };
}

/**
 * Enables horizontal scrolling with the vertical mouse wheel.
 */
function enableHorizontalWheelScroll(el) {
    el.addEventListener('wheel', (e) => {
        if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
            el.scrollLeft += e.deltaY;
            e.preventDefault();
        }
    }, { passive: false });
}

/**
 * Main initialization function.
 */
(async function init() {
    document.body.classList.add('is-init');

    [state.champions, state.models] = await Promise.all([
        loadList('static/champions.txt'),
        loadList('static/models.txt')
    ]);

    addCharacter({}, { animate: false });
    addCharacter({}, { animate: false });

    const storyTextarea = $('#story');
    const charCount = $('#charCount');
    const storyHint = $('#storyHint');

    storyTextarea.addEventListener('input', () => {
        const length = storyTextarea.value.length;
        charCount.textContent = `${length} / 500`;

        if (storyHint) {
            storyHint.style.display = length > 0 ? 'none' : 'block';
        }

        validateForm();
        markValidity();
    });

    markValidity();

    $('#addCharBtn').addEventListener('click', () => addCharacter());

    $('#submitBtn').addEventListener('click', () => {
        if (!validateForm()) {
            markValidity();
            toast('⚠️ Please fix the errors before submitting.');

            const firstInvalid = $('textarea.invalid, .char-card.invalid');
            if (firstInvalid) {
                if (firstInvalid.tagName === 'TEXTAREA') {
                    firstInvalid.focus();
                } else {
                    const input = firstInvalid.querySelector('input');
                    if (input) input.focus();
                }
            }
            return;
        }

        const payload = buildPayload();
        payload.retry_count = state.retryCount;  // Include retry count
        
        console.log('--- FORM SUBMITTED ---');
        console.log(JSON.stringify(payload, null, 2));

        const submitBtn = $('#submitBtn');
        const feedbackDiv = $('#validationFeedback');
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        // Send the payload to the Flask backend
        fetch('/submit-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Server response:', data);
            
            if (data.needs_retry) {
                // Story validation failed, show feedback
                state.retryCount = data.retry_count;
                
                feedbackDiv.textContent = `⚠️ ${data.feedback} (Attempt ${data.retry_count}/3)`;
                feedbackDiv.style.display = 'block';
                toast(`⚠️ ${data.feedback}`);
                
            } else if (data.auto_generated) {
                // Max retries reached, story was auto-generated
                state.retryCount = 0;
                
                const storyTextarea = $('#story');
                storyTextarea.value = data.generated_story;
                
                feedbackDiv.textContent = `ℹ️ ${data.message} Please review and submit again.`;
                feedbackDiv.style.display = 'block';
                feedbackDiv.style.background = '#d1ecf1';
                feedbackDiv.style.borderColor = '#17a2b8';
                feedbackDiv.style.color = '#0c5460';
                toast('ℹ️ Story generated. Please review and submit.');
                
            } else if (data.success) {
                // Story generation started successfully
                state.retryCount = 0;
                toast('✅ Story generation started!');
                feedbackDiv.style.display = 'none';
                
            } else {
                // Other error
                toast('❌ Server failed to process request.');
            }
        })
        .catch(error => {
            console.error('Network error:', error);
            toast('❌ Network error during submission.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Configuration';
        });
    });

    const carousel = $('#charCarousel');
    if (carousel) {
        enableHorizontalWheelScroll(carousel);

        const fadeLeft = $('.fade-left');
        const fadeRight = $('.fade-right');
        carousel.addEventListener('scroll', () => {
            const scrollLeft = carousel.scrollLeft;
            const maxScroll = carousel.scrollWidth - carousel.clientWidth;
            fadeLeft.style.display = scrollLeft > 10 ? 'block' : 'none';
            fadeRight.style.display = scrollLeft < (maxScroll - 10) ? 'block' : 'none';
        }, { passive: true });
    }

    setTimeout(() => {
        document.body.classList.remove('is-init');
    }, 100);
})();