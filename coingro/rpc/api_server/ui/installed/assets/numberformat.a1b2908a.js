function t(n){return n==null}function o(n,r=3){return t(n)?"":`${(n*100).toFixed(r)}%`}function e(n,r=15){return t(n)?"N/A":n.toLocaleString("fullwide",{useGrouping:!1,maximumFractionDigits:r})}function u(n,r,i=3){return`${e(n,i)} ${r}`}export{u as a,e as b,o as f};
//# sourceMappingURL=numberformat.a1b2908a.js.map
