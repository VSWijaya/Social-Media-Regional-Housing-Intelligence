document.addEventListener("DOMContentLoaded", () => {
  // =====================================================
  // SETTINGS
  // =====================================================

  const DATA_FILE = "suburb_data.json";

  // ABS Census context (made by abs_to_json.py)
  const CONTEXT_FILE = "abs_suburb_context.json";

  const SIDEBAR_STORAGE_KEY = "sidebarCollapsed";

  let suburbData = [];

  // Suburb name -> ABS context record
  let contextData = {};

  // =====================================================
  // SIDEBAR
  // =====================================================

  const dashboard = document.getElementById("dashboard");

  const sidebarToggle = document.getElementById("sidebarToggle");

  function loadSidebarState() {
    try {
      return localStorage.getItem(SIDEBAR_STORAGE_KEY) === "true";
    } catch (error) {
      console.warn("Could not load sidebar state.");

      return false;
    }
  }

  function saveSidebarState(collapsed) {
    try {
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
    } catch (error) {
      console.warn("Could not save sidebar state.");
    }
  }

  function updateSidebar(collapsed) {
    if (!dashboard || !sidebarToggle) {
      return;
    }

    dashboard.classList.toggle("sidebar-collapsed", collapsed);

    sidebarToggle.setAttribute("aria-expanded", String(!collapsed));

    sidebarToggle.setAttribute(
      "aria-label",
      collapsed ? "Expand sidebar" : "Collapse sidebar"
    );

    sidebarToggle.title = collapsed ? "Expand sidebar" : "Collapse sidebar";

    saveSidebarState(collapsed);
  }

  if (dashboard && sidebarToggle) {
    updateSidebar(loadSidebarState());

    sidebarToggle.addEventListener("click", () => {
      const isCollapsed = dashboard.classList.contains("sidebar-collapsed");

      updateSidebar(!isCollapsed);
    });
  }

  // =====================================================
  // HELPER FUNCTIONS
  // =====================================================

  function escapeHTML(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Same function under the lowercase name, so either spelling works
  const escapeHtml = escapeHTML;

  function scoreClass(score) {
    const number = Number(score);

    if (number >= 0.05) {
      return "positive";
    }

    if (number <= -0.05) {
      return "negative";
    }

    return "neutral";
  }

  function labelClass(label) {
    const normalized = String(label).toLowerCase();

    if (normalized === "positive") {
      return "positive";
    }

    if (normalized === "negative") {
      return "negative";
    }

    return "neutral";
  }

  function formatScore(score) {
    const number = Number(score);

    return `${number >= 0 ? "+" : ""}${number.toFixed(2)}`;
  }

  // Bar widths are stored as data-width="42" in the HTML and
  // applied here, instead of writing style="width: ${...}%" inline.
  function applyBarWidths(container) {
    container.querySelectorAll("[data-width]").forEach((element) => {
      const width = Math.max(
        0,
        Math.min(100, Number(element.dataset.width) || 0)
      );

      element.style.width = `${width}%`;
    });
  }

  function topicIcon(topic) {
    const normalized = String(topic).toLowerCase();

    if (normalized.includes("lifestyle")) {
      return {
        icon: "fa-seedling",

        className: "green"
      };
    }

    if (normalized.includes("education")) {
      return {
        icon: "fa-graduation-cap",

        className: "blue"
      };
    }

    if (normalized.includes("crime")) {
      return {
        icon: "fa-shield-halved",

        className: "orange"
      };
    }

    if (normalized.includes("afford")) {
      return {
        icon: "fa-dollar-sign",

        className: "gold"
      };
    }

    return {
      icon: "fa-circle-info",

      className: "blue"
    };
  }

  // =====================================================
  // TOPIC HELPERS
  // =====================================================

  const TOPIC_NAMES = [
    "Lifestyle & Amenities",
    "Crime & Safety",
    "Education & Employment",
    "Affordability"
  ];

  // "Crime and Safety", "Crime & Safety" and "crime  safety"
  // all become "crimesafety", so button names and JSON keys match.
  function normaliseTopic(name) {
    return String(name || "")
      .toLowerCase()
      .replace(/\band\b/g, "")
      .replace(/[^a-z]/g, "");
  }

  function topicDisplayName(topic) {
    return (
      TOPIC_NAMES.find(
        (name) => normaliseTopic(name) === normaliseTopic(topic)
      ) || topic
    );
  }

  function getTopic(suburb, topicName) {
    const topics = suburb.topics || {};

    const key = Object.keys(topics).find((name) => {
      return normaliseTopic(name) === normaliseTopic(topicName);
    });

    return key ? topics[key] : null;
  }

  // A topic only counts if at least one post talked about it
  function isDiscussed(topic) {
    return Boolean(topic) && Number(topic.post_count) > 0;
  }

  // Posts and comments shown together as one number
  function totalPosts(suburb) {
    return Number(suburb.post_count || 0) + Number(suburb.comment_count || 0);
  }

  // Splits a suburb's topics into strengths, neutral, concerns
  // and topics nobody talked about.
  function groupSuburbTopics(suburb) {
    const groups = {
      strengths: [],
      neutral: [],
      concerns: [],
      notDiscussed: []
    };

    const extraTopics = Object.keys(suburb.topics || {}).filter((name) => {
      return !TOPIC_NAMES.some(
        (known) => normaliseTopic(known) === normaliseTopic(name)
      );
    });

    [...TOPIC_NAMES, ...extraTopics].forEach((name) => {
      const topic = getTopic(suburb, name);

      if (!isDiscussed(topic)) {
        groups.notDiscussed.push(name);
        return;
      }

      const type = labelClass(topic.label);

      if (type === "positive") {
        groups.strengths.push(topic);
      } else if (type === "negative") {
        groups.concerns.push(topic);
      } else {
        groups.neutral.push(topic);
      }
    });

    groups.strengths.sort((a, b) => b.average_score - a.average_score);
    groups.concerns.sort((a, b) => a.average_score - b.average_score);
    groups.neutral.sort((a, b) => b.post_count - a.post_count);

    return groups;
  }

  // =====================================================
  // LOAD JSON DATA
  // =====================================================

  async function loadData() {
    try {
      const response = await fetch(DATA_FILE);

      if (!response.ok) {
        throw new Error(
          `Could not load ${DATA_FILE}. Status: ${response.status}`
        );
      }

      const data = await response.json();

      showUpdatedYear(data, response);

      if (!Array.isArray(data.suburb_summary)) {
        throw new Error("suburb_summary is missing from the JSON file.");
      }

      suburbData = data.suburb_summary;

      const currentPage = document.body.dataset.page;

      // ABS context is only shown on the suburb page
      if (currentPage === "suburb") {
        await loadContextData();
      }

      if (currentPage === "overall") {
        initialiseOverallPage();
      }

      if (currentPage === "suburb") {
        initialiseSuburbPage();
      }
    } catch (error) {
      console.error("Error loading JSON:", error);

      showDataError(error);
    }
  }

  // Shows "Updated 2026" in the header.
  // 1st choice: a "last_updated" (or "lastUpdated"/"lastupdated"/"updated_at"/"generated_at") field
  //             at the top of the JSON, e.g. "last_updated": "2026-10-18"
  // 2nd choice: the date the JSON file was last saved (from the server)
  function showUpdatedYear(data, response) {
    const label = document.getElementById("dataUpdated");

    if (!label) {
      return;
    }

    const rawDate =
      data.last_updated ||
      data.lastUpdated ||
      data.lastupdated ||
      data.updated_at ||
      data.generated_at ||
      response.headers.get("Last-Modified");

    const date = rawDate ? new Date(rawDate) : null;

    if (!date || Number.isNaN(date.getTime())) {
      label.textContent = "Updated —";
      return;
    }

    label.textContent = `Updated ${date.getFullYear()}`;

    // Full date when hovering over the button
    label.parentElement.title = `Last updated ${date.toLocaleDateString(
      "en-AU",
      {
        day: "numeric",
        month: "long",
        year: "numeric"
      }
    )}`;
  }

  // Loads the ABS file. If it is missing, the page still works
  // and the Suburb Context section shows "not available".
  async function loadContextData() {
    try {
      const response = await fetch(CONTEXT_FILE);

      if (!response.ok) {
        throw new Error(`Status: ${response.status}`);
      }

      const data = await response.json();

      (data.suburb_context || []).forEach((item) => {
        contextData[item.suburb] = item;
      });
    } catch (error) {
      console.warn(`Could not load ${CONTEXT_FILE}:`, error);
    }
  }

  // Shows a helpful message when suburb_data.json cannot be loaded.
  // Opening the HTML file directly (file://) blocks fetch(), so that
  // case gets its own instruction.
  function showDataError(error) {
    const openedAsFile = window.location.protocol === "file:";

    const reason = openedAsFile
      ? "The page was opened directly from your computer, which blocks the data file from loading. Open it through a local server instead (for example, VS Code Live Server)."
      : `Make sure ${DATA_FILE} is in the same folder as index.html and is valid JSON.`;

    const detail = error && error.message ? error.message : "";

    const messageHTML = `
      <strong>Could not load ${escapeHTML(DATA_FILE)}.</strong>
      <br><br>
      ${escapeHTML(reason)}
      ${detail ? `<br><br><small>${escapeHTML(detail)}</small>` : ""}
    `;

    const tableBody = document.getElementById("suburbTableBody");

    if (tableBody) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" class="loading-cell">${messageHTML}</td>
        </tr>
      `;
    }

    document.querySelectorAll(".loading-card").forEach((card) => {
      card.innerHTML = `<div>${messageHTML}</div>`;
    });
  }

  // =====================================================
  // OVERALL VIEW
  // =====================================================

  function initialiseOverallPage() {
    const topicButtons = document.querySelectorAll(".topic-button");

    renderRankingTable("all");

    topicButtons.forEach((button) => {
      button.addEventListener("click", () => {
        topicButtons.forEach((item) => {
          item.classList.remove("selected");
        });

        button.classList.add("selected");

        renderRankingTable(button.dataset.topic || "all");
      });
    });
  }

  // =====================================================
  // RENDER OVERALL TABLE
  // =====================================================

  // "all"  -> rank by overall sentiment
  // topic  -> rank by that topic's score; suburbs that never
  //           discussed it go to the bottom, unranked
  function buildRankingRows(topic) {
    return suburbData.map((suburb) => {
      if (topic === "all") {
        return {
          suburb,
          score: Number(suburb.overall_sentiment_score),
          label: suburb.sentiment_label,
          discussed: true
        };
      }

      const topicData = getTopic(suburb, topic);

      if (!isDiscussed(topicData)) {
        return { suburb, score: null, label: null, discussed: false };
      }

      return {
        suburb,
        score: Number(topicData.average_score),
        label: topicData.label,
        discussed: true
      };
    });
  }

  function renderRankingTable(topic = "all") {
    const tableBody = document.getElementById("suburbTableBody");

    if (!tableBody) {
      return;
    }

    const scoreHeader = document.querySelector(
      ".ranking-section thead th:nth-child(3)"
    );

    if (scoreHeader) {
      scoreHeader.textContent =
        topic === "all"
          ? "Sentiment Score"
          : `${topicDisplayName(topic)} Score`;
    }

    const rows = buildRankingRows(topic);

    const discussed = rows
      .filter((row) => row.discussed)
      .sort((a, b) => b.score - a.score);

    const notDiscussed = rows
      .filter((row) => !row.discussed)
      .sort((a, b) => a.suburb.suburb.localeCompare(b.suburb.suburb));

    if (rows.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" class="loading-cell">No suburb data available.</td>
        </tr>
      `;

      return;
    }

    const discussedHTML = discussed
      .map((row, index) => renderRankingRow(row, index + 1))
      .join("");

    const notDiscussedHTML = notDiscussed
      .map((row) => renderRankingRow(row, null))
      .join("");

    tableBody.innerHTML = discussedHTML + notDiscussedHTML;

    applyBarWidths(tableBody);
  }

  function renderRankingRow(row, rank) {
    const name = row.suburb.suburb;

    const detailLink = `suburb.html?left=${encodeURIComponent(name)}`;

    const actionHTML = `
      <td>
        <a class="view-detail-button" href="${detailLink}">
          View Detail
          <i class="fa-solid fa-chevron-right"></i>
        </a>
      </td>
    `;

    if (!row.discussed) {
      return `
        <tr class="row-not-discussed">
          <td><span class="rank-badge muted">–</span></td>
          <td><span class="suburb-name">${escapeHTML(name)}</span></td>
          <td>
            <div class="score-display">
              <span class="score-number not-discussed">–</span>
            </div>
          </td>
          <td><span class="sentiment-pill not-discussed">Not discussed</span></td>
          ${actionHTML}
        </tr>
      `;
    }

    const scoreType = row.label ? labelClass(row.label) : scoreClass(row.score);

    const sentimentType = labelClass(row.label);

    // Centre-zero bar: the middle line is 0, negative scores grow
    // to the left and positive scores grow to the right.
    // Each half of the track represents 0 to 1, so the width is
    // |score| x 50% of the whole track.
    const scoreWidth = Math.max(2, Math.round(Math.abs(row.score) * 50));

    const scoreSide = row.score < 0 ? "left" : "right";

    return `
      <tr>
        <td>
          <span class="rank-badge ${rank === 1 ? "top-rank" : ""}">${rank}</span>
        </td>
        <td><span class="suburb-name">${escapeHTML(name)}</span></td>
        <td>
          <div class="score-display">
            <span class="score-number ${scoreType}">${formatScore(row.score)}</span>
            <div
              class="score-track"
              title="Centre line = 0. Left = negative, right = positive."
            >
              <div class="score-fill ${scoreType} ${scoreSide}" data-width="${scoreWidth}"></div>
            </div>
          </div>
        </td>
        <td>
          <span class="sentiment-pill ${sentimentType}">${escapeHTML(row.label)}</span>
        </td>
        ${actionHTML}
      </tr>
    `;
  }

  // =====================================================
  // SUBURB VIEW
  // =====================================================

  function initialiseSuburbPage() {
    const leftSelect = document.getElementById("leftSuburbSelect");

    const rightSelect = document.getElementById("rightSuburbSelect");

    const swapButton = document.getElementById("swapSuburbs");

    if (!leftSelect || !rightSelect) {
      return;
    }

    // ===================================================
    // CREATE DROPDOWN OPTIONS
    // ===================================================

    const suburbOptions = suburbData
      .map((suburb) => {
        return `

              <option
                value="${escapeHTML(suburb.suburb)}"
              >

                ${escapeHTML(suburb.suburb)}

              </option>

            `;
      })
      .join("");

    leftSelect.innerHTML = suburbOptions;

    rightSelect.innerHTML = suburbOptions;

    // ===================================================
    // GET VALUES FROM URL
    // ===================================================

    const params = new URLSearchParams(window.location.search);

    const requestedLeft = params.get("left");

    const requestedRight = params.get("right");

    // ===================================================
    // DEFAULT LEFT SUBURB
    // ===================================================

    const leftExists = suburbData.some((suburb) => {
      return suburb.suburb === requestedLeft;
    });

    const defaultLeft = leftExists ? requestedLeft : suburbData[0]?.suburb;

    // ===================================================
    // DEFAULT RIGHT SUBURB
    // ===================================================

    const rightExists = suburbData.some((suburb) => {
      return suburb.suburb === requestedRight;
    });

    let defaultRight;

    if (rightExists) {
      defaultRight = requestedRight;
    } else {
      defaultRight =
        suburbData.find((suburb) => {
          return suburb.suburb !== defaultLeft;
        })?.suburb || suburbData[0]?.suburb;
    }

    // ===================================================
    // SET INITIAL DROPDOWN VALUES
    // ===================================================

    leftSelect.value = defaultLeft;

    rightSelect.value = defaultRight;

    // ===================================================
    // DISPLAY INITIAL CARDS
    // ===================================================

    refreshComparison();

    // ===================================================
    // LEFT DROPDOWN CHANGE
    // ===================================================

    // Remember the last values, so choosing the suburb that is
    // already on the other side swaps the two instead.
    let previousLeft = leftSelect.value;

    let previousRight = rightSelect.value;

    function rememberSelection() {
      previousLeft = leftSelect.value;

      previousRight = rightSelect.value;
    }

    leftSelect.addEventListener("change", () => {
      if (leftSelect.value === rightSelect.value) {
        rightSelect.value = previousLeft;
      }

      rememberSelection();

      refreshComparison();

      updateComparisonURL(leftSelect.value, rightSelect.value);
    });

    // ===================================================
    // RIGHT DROPDOWN CHANGE
    // ===================================================

    rightSelect.addEventListener("change", () => {
      if (rightSelect.value === leftSelect.value) {
        leftSelect.value = previousRight;
      }

      rememberSelection();

      refreshComparison();

      updateComparisonURL(leftSelect.value, rightSelect.value);
    });

    // ===================================================
    // SWAP BUTTON
    // ===================================================

    if (swapButton) {
      swapButton.addEventListener("click", () => {
        // Save old values
        const oldLeft = leftSelect.value;

        const oldRight = rightSelect.value;

        // Swap dropdown values
        leftSelect.value = oldRight;

        rightSelect.value = oldLeft;

        rememberSelection();

        // Re-render cards
        refreshComparison();

        // Update URL
        updateComparisonURL(leftSelect.value, rightSelect.value);

        // Small animation
        swapButton.classList.add("swap-active");

        setTimeout(() => {
          swapButton.classList.remove("swap-active");
        }, 250);
      });
    }

    // ===================================================
    // REFRESH BOTH CARDS
    // ===================================================

    function refreshComparison() {
      const leftSuburb = findSuburb(leftSelect.value);

      const rightSuburb = findSuburb(rightSelect.value);

      renderSuburbCard("leftSuburbCard", leftSuburb);

      renderSuburbCard("rightSuburbCard", rightSuburb);
    }
  }

  // =====================================================
  // FIND SUBURB
  // =====================================================

  function findSuburb(name) {
    return suburbData.find((suburb) => {
      return suburb.suburb === name;
    });
  }

  // =====================================================
  // UPDATE URL
  // =====================================================

  function updateComparisonURL(leftSuburb, rightSuburb) {
    const url = new URL(window.location.href);

    url.searchParams.set("left", leftSuburb);

    url.searchParams.set("right", rightSuburb);

    window.history.replaceState({}, "", url);
  }

  // =====================================================
  // RENDER SUBURB CARD
  // =====================================================

  function renderSuburbCard(cardId, suburb) {
    const card = document.getElementById(cardId);

    if (!card || !suburb) {
      return;
    }

    const score = Number(suburb.overall_sentiment_score);

    const scoreType = suburb.sentiment_label
      ? labelClass(suburb.sentiment_label)
      : scoreClass(score);

    const sentimentType = labelClass(suburb.sentiment_label);

    const breakdown = suburb.sentiment_breakdown || {};

    const groups = groupSuburbTopics(suburb);

    const postTotal = totalPosts(suburb);

    card.innerHTML = `
      <!-- CARD HEADER -->
      <div class="suburb-card-header">
        <div class="suburb-card-title">
          <i class="fa-solid fa-location-dot"></i>
          <h2>${escapeHTML(suburb.suburb)}</h2>
        </div>

        <span
          class="posts-badge"
          title="${Number(suburb.post_count || 0)} posts + ${Number(suburb.comment_count || 0)} comments"
        >
          ${postTotal.toLocaleString("en-AU")} posts
        </span>
      </div>

      <!-- SCORE -->
      <div class="score-summary ${scoreType}">
        <div>
          <span class="small-label">Sentiment Score</span>

          <div class="large-score ${scoreType}">
            ${formatScore(score)}
            <small>/1.0</small>
          </div>
        </div>

        <span class="sentiment-pill ${sentimentType}">
          ${escapeHTML(suburb.sentiment_label)}
        </span>
      </div>

      <!-- SENTIMENT BREAKDOWN -->
      <div class="sentiment-statistics">
        ${renderSentimentRow("Positive", breakdown.positive_pct || 0, "progress-positive")}
        ${renderSentimentRow("Neutral", breakdown.neutral_pct || 0, "progress-neutral")}
        ${renderSentimentRow("Negative", breakdown.negative_pct || 0, "progress-negative")}
      </div>

      <div class="card-divider"></div>

      ${renderInsightGroup("Top Strengths", "What residents value", groups.strengths, "strength")}

      ${renderInsightGroup("Top Concerns", "What residents are concerned about", groups.concerns, "concern")}

      ${renderInsightGroup("Neutral", "Mixed or balanced opinions", groups.neutral, "neutral")}

      ${renderNotDiscussed(groups.notDiscussed)}

      <!-- SUBURB CONTEXT (ABS) -->
      <div class="card-divider"></div>

      ${renderSuburbContext(contextData[suburb.suburb])}
    `;

    applyBarWidths(card);
  }

  // =====================================================
  // RENDER SUBURB CONTEXT (ABS CENSUS)
  // =====================================================

  function renderSuburbContext(context) {
    const header = `
      <div class="insight-heading">
        <div>
          <span class="small-label">Suburb Context</span>
          <h3>ABS Census data</h3>
        </div>
        <i class="fa-solid fa-chart-simple context-heading-icon"></i>
      </div>
    `;

    if (!context) {
      return `
        <section class="suburb-context">
          ${header}
          <div class="empty-insight">No ABS data available.</div>
        </section>
      `;
    }

    const money = (value) =>
      value == null ? "–" : `$${Number(value).toLocaleString("en-AU")}/wk`;

    const percent = (value, decimals = 0) =>
      value == null ? "–" : `${Number(value).toFixed(decimals)}%`;

    const stats = [
      [money(context.household_income_weekly_aud), "Household income"],
      [percent(context.families_with_children_pct), "Families with children"],
      [percent(context.unemployment_pct, 1), "Unemployment"],
      [money(context.median_rent_weekly_aud), "Median rent"],
      [
        context.median_age_years == null
          ? "–"
          : `${context.median_age_years} yrs`,
        "Median age"
      ],
      [percent(context.bachelor_plus_pct), "Bachelor+"]
    ];

    const statsHTML = stats
      .map(
        ([value, label]) => `
          <div class="context-stat">
            <strong>${escapeHTML(value)}</strong>
            <span>${escapeHTML(label)}</span>
          </div>
        `
      )
      .join("");

    const bands = Array.isArray(context.age_distribution)
      ? context.age_distribution
      : [];

    const segmentsHTML = bands
      .map((band, index) => {
        const pct = Math.max(0, Number(band.pct) || 0);

        return `
          <div
            class="age-segment age-segment-${index + 1}"
            data-width="${pct}"
            title="${escapeHTML(band.band)}: ${pct}%"
          ></div>
        `;
      })
      .join("");

    const legendHTML = bands
      .map(
        (band, index) => `
          <span class="age-legend-item">
            <i class="age-swatch age-segment-${index + 1}"></i>
            ${escapeHTML(band.band)}
            <strong>${Number(band.pct).toFixed(0)}%</strong>
          </span>
        `
      )
      .join("");

    return `
      <section class="suburb-context">
        ${header}

        <div class="context-grid">
          ${statsHTML}
        </div>

        ${
          bands.length
            ? `
          <div class="age-distribution">
            <span class="small-label">Age distribution</span>
            <div class="age-bar">${segmentsHTML}</div>
            <div class="age-legend">${legendHTML}</div>
          </div>
        `
            : ""
        }

        <p class="context-source">
          Source: ABS Census ${escapeHTML(context.census_year || 2021)}
        </p>
      </section>
    `;
  }

  // =====================================================
  // RENDER SENTIMENT ROW
  // =====================================================

  function renderSentimentRow(label, percentage, progressClass) {
    const safePercentage = Math.max(0, Math.min(100, Number(percentage)));

    return `

      <div
        class="sentiment-row"
      >


        <span>

          ${escapeHTML(label)}

        </span>



        <div
          class="progress-bar"
        >

          <div
            class="
              progress-value
              ${progressClass}
            "
            data-width="${safePercentage}"
          ></div>

        </div>



        <strong>

          ${safePercentage}%

        </strong>


      </div>

    `;
  }

  // =====================================================
  // RENDER STRENGTH / CONCERN SECTION
  // =====================================================

  const INSIGHT_TYPES = {
    strength: {
      groupClass: "",
      icon: "fa-arrow-trend-up strength-heading-icon",
      empty: "No clear strengths yet."
    },
    neutral: {
      groupClass: "neutral-group",
      icon: "fa-scale-balanced neutral-heading-icon",
      empty: "No neutral topics."
    },
    concern: {
      groupClass: "concerns",
      icon: "fa-triangle-exclamation concern-heading-icon",
      empty: "No major concerns."
    }
  };

  function renderInsightGroup(eyebrow, title, items, type) {
    const settings = INSIGHT_TYPES[type] || INSIGHT_TYPES.strength;

    const content =
      items.length === 0
        ? `<div class="empty-insight">${escapeHTML(settings.empty)}</div>`
        : items.map((item) => renderInsightItem(item)).join("");

    return `
      <section class="insight-group ${settings.groupClass}">
        <div class="insight-heading">
          <div>
            <span class="small-label">${escapeHTML(eyebrow)}</span>
            <h3>${escapeHTML(title)}</h3>
          </div>

          <i class="fa-solid ${settings.icon}"></i>
        </div>

        ${content}
      </section>
    `;
  }

  // =====================================================
  // RENDER INDIVIDUAL INSIGHT
  // =====================================================

  function renderInsightItem(item) {
    const iconInfo = topicIcon(item.topic);

    const keywords = Array.isArray(item.keywords) ? item.keywords : [];

    const tone = labelClass(item.label);

    return `
      <div class="insight-item">
        <div class="insight-icon ${iconInfo.className}">
          <i class="fa-solid ${iconInfo.icon}"></i>
        </div>

        <div class="insight-content">
          <div class="insight-title">
            <strong>${escapeHTML(item.topic)}</strong>

            <span>
              <span class="insight-score ${tone}">${formatScore(item.average_score)}</span>
              · ${Number(item.post_count || 0)} posts
            </span>
          </div>

          <div class="keywords">
            ${keywords.map((keyword) => `<span>${escapeHTML(keyword)}</span>`).join("")}
          </div>
        </div>
      </div>
    `;
  }

  // =====================================================
  // RENDER "NOT DISCUSSED" TOPICS
  // =====================================================

  function renderNotDiscussed(names) {
    if (names.length === 0) {
      return "";
    }

    // Same markup as Strengths / Concerns, so it uses the same card styling
    const items = names
      .map((name) => {
        const iconInfo = topicIcon(name);

        return `
          <div class="insight-item not-discussed-item">
            <div class="insight-icon ${iconInfo.className}">
              <i class="fa-solid ${iconInfo.icon}"></i>
            </div>

            <div class="insight-content">
              <div class="insight-title">
                <strong>${escapeHTML(name)}</strong>
                <span>0 posts</span>
              </div>

              <div class="keywords">
                <span>Not discussed yet</span>
              </div>
            </div>
          </div>
        `;
      })
      .join("");

    return `
      <section class="insight-group not-discussed-group">
        <div class="insight-heading">
          <div>
            <span class="small-label">Not Discussed</span>
            <h3>No posts mention these yet</h3>
          </div>

          <i class="fa-regular fa-comment-dots not-discussed-heading-icon"></i>
        </div>

        ${items}
      </section>
    `;
  }

  // =====================================================
  // START APPLICATION
  // =====================================================

  loadData();
});
