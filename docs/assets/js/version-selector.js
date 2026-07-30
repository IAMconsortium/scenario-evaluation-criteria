/*
 * Mirrors the mike/mkdocs-material version selector (rendered into
 * `.md-header .md-version` once versions.json has loaded) into any
 * element carrying a `data-md-version-embed` attribute, so the same
 * dropdown can appear inside the page content as well as the header.
 * Elements carrying `data-md-version-label` are filled with the
 * current version's title.
 */
document.addEventListener("DOMContentLoaded", function () {
  var targets = document.querySelectorAll("[data-md-version-embed]");
  var labels = document.querySelectorAll("[data-md-version-label]");
  if (!targets.length && !labels.length) {
    return;
  }

  function currentTitle(source) {
    var button = source.querySelector(".md-version__current");
    if (!button) {
      return "";
    }
    var text = "";
    button.childNodes.forEach(function (node) {
      if (node.nodeType === Node.TEXT_NODE) {
        text += node.textContent;
      }
    });
    return text.trim();
  }

  function clone() {
    var source = document.querySelector(".md-header .md-version");
    if (!source) {
      return false;
    }
    targets.forEach(function (target) {
      target.innerHTML = "";
      target.appendChild(source.cloneNode(true));
    });
    var title = currentTitle(source);
    labels.forEach(function (label) {
      label.textContent = title;
    });
    return true;
  }

  if (clone()) {
    return;
  }

  var header = document.querySelector(".md-header");
  if (!header) {
    return;
  }

  var observer = new MutationObserver(function () {
    if (clone()) {
      observer.disconnect();
    }
  });
  observer.observe(header, { childList: true, subtree: true });
});
