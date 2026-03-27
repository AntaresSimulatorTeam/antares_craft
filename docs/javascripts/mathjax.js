window.MathJax = {
  loader: {load: ['[tex]/mhchem']},
  tex: {
    packages: {'[+]': ['mhchem']},
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
  },
};

document$.subscribe(() => {
  MathJax.startup.promise.then(() => {
    MathJax.typesetPromise();
  });
});