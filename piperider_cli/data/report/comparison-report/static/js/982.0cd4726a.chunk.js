"use strict";(self.webpackChunk_infuseai_piperider_ui=self.webpackChunk_infuseai_piperider_ui||[]).push([[982],{1982:function(e,n,t){t.r(n),t.d(n,{SRPage:function(){return U},default:function(){return H}});var i=t(2904),s=t(8794),l=t(3851),a=t(1288),r=t(3182),o=t(1831),d=t(5322),x=t(1431),c=t(7615),u=t(6830),j=t(1756),h=t(1676),v=t(2158),m=t(6564),p=t(2122),f=t(7437),b=t(3510),g=t(5887);function y(){var e,n,t;(0,p.mq)({eventName:o.FP.PAGE_VIEW,eventProperties:{type:o.ll,page:"assertion-list-page"}});var i=(0,j.useState)(""),s=(0,x.Z)(i,2),l=s[0],a=s[1],r=o.nq.getState().assertionsOnly,d=(r||{}).metadata;return(0,g.jsxs)(c.xu,{children:[(0,g.jsxs)(u.bZ,{status:"warning",mb:5,children:[(0,g.jsx)(u.zM,{}),(0,g.jsxs)(c.xu,{children:[(0,g.jsx)(u.Cd,{children:"The Assertions page is deprecated and will be removed in the future"}),(0,g.jsxs)(u.X,{fontSize:"sm",children:["If you have a strong need for this page, please contact us by the"," ",(0,g.jsx)(c.rU,{href:b.p,style:{textDecoration:"underline"},children:"feedback link"}),". Your feedback is important to us. Thank you!"]})]})]}),(0,g.jsx)(c.xv,{fontSize:"xl",fontWeight:"semibold",textAlign:"left",children:"Assertions"}),(0,g.jsx)(c.kC,{maxW:f.eb-50,w:"100%",children:(0,g.jsx)(v.f,{onChange:a,filterString:l})}),(0,g.jsx)(c.kC,{justify:"start",maxW:f.eb-50,w:"100%",my:5,children:Number(null===d||void 0===d||null===(e=d.base)||void 0===e?void 0:e.total)>0&&(0,g.jsx)(h.F,{total:null===d||void 0===d||null===(n=d.base)||void 0===n?void 0:n.total,failed:null===d||void 0===d||null===(t=d.base)||void 0===t?void 0:t.failed})}),(0,g.jsx)(m.O,{maxW:f.eb-50,w:"100%",singleOnly:!0,filterString:l,comparableAssertions:r})]})}var C=t(4163);function w(){var e,n;(0,p.mq)({eventName:o.FP.PAGE_VIEW,eventProperties:{type:o.ll,page:"metrics-page"}});var t=o.nq.getState().BMOnly;return(0,g.jsxs)(c.xu,{children:[(0,g.jsx)(c.xv,{fontSize:"xl",fontWeight:"semibold",textAlign:"left",children:"Metrics"}),(0,g.jsxs)(c.rj,{templateColumns:{base:"1fr",xl:"1fr 1fr"},w:"100%",gap:5,children:[(null!==(e=null===t||void 0===t?void 0:t.base)&&void 0!==e?e:[]).map((function(e){return(0,g.jsx)(c.P4,{children:(0,g.jsx)(C.l,{data:{base:e},singleOnly:!0})},e.name)})),!(null!==t&&void 0!==t&&null!==(n=t.base)&&void 0!==n&&n.length)&&(0,g.jsx)(s.Jd,{text:"No metrics data available"})]})]})}var S=t(2471),W=t(7708),A=t(4641),z=t(962),D=t(3512),P=t(3214),N=t(8685),k=t(421),E=t(6629);function T(){var e=(0,i.yj)(d.t3),n=(0,x.Z)(e,2)[1],t=decodeURIComponent((null===n||void 0===n?void 0:n.tableName)||""),s=decodeURIComponent((null===n||void 0===n?void 0:n.columnName)||"");(0,N.mq)({eventName:N.FP.PAGE_VIEW,eventProperties:{type:N.ll,page:"column-details-page"}});var l=E.n.getState(),a=l.tableColumnsOnly,r=void 0===a?[]:a,o=l.rawData.base,u=r.find((function(e){return(0,x.Z)(e,1)[0]===t})),j=null===o||void 0===o?void 0:o.tables[t],h=null===j||void 0===j?void 0:j.columns,v=h?h[s]:void 0,m=v||{},p=m.type,f=m.histogram,b=m.schema_type,y=(0,P.MM)(v),C=y.backgroundColor,w=y.icon;if(!t||!j||!u||!v)return(0,g.jsx)(D.J,{text:"No profile data found for '".concat(t,".").concat(s,"'")});var T=(0,P.hG)(p);return(0,g.jsxs)(g.Fragment,{children:[(0,g.jsx)(k.Q,{title:s,subtitle:b,infoTip:null===v||void 0===v?void 0:v.description,icon:w,iconColor:C,mb:5}),(0,g.jsxs)(c.rj,{width:"100%",templateColumns:{base:"1fr",xl:"1fr 1px 1fr"},gap:5,children:[(0,g.jsxs)(c.gC,{spacing:10,flex:"1",width:"100%",flexGrow:1,flexShrink:1,children:[(0,g.jsxs)(c.xu,{width:"100%",children:[(0,g.jsx)(c.xv,{fontSize:"xl",children:"Data Composition"}),(0,g.jsx)(c.iz,{}),(0,g.jsx)(S.t,{columnDatum:v})]}),(0,P.jl)(p)&&(0,g.jsxs)(c.xu,{width:"100%",children:[(0,g.jsxs)(c.xv,{fontSize:"xl",children:[v?(0,N.B1)(null===v||void 0===v?void 0:v.type):"Type "," ","Statistics"]}),(0,g.jsx)(c.iz,{}),(0,g.jsx)(z.E,{columnDatum:v})]}),T&&f&&(0,g.jsxs)(c.xu,{width:"100%",children:[(0,g.jsx)(c.xv,{fontSize:"xl",children:"Quantile Data"}),(0,g.jsx)(c.iz,{}),(0,g.jsx)(A.M,{columnDatum:v})]})]}),(0,g.jsx)(c.iz,{orientation:"vertical"}),(0,g.jsx)(c.gC,{spacing:10,width:"100%",children:(0,g.jsx)(W.r,{columnDatum:v})})]})]})}function F(){var e=(0,i.TH)(),n=(0,x.Z)(e,2),t=n[0],s=n[1];return(0,j.useEffect)((function(){t&&"/"!==t||s("/tables")}),[t,s]),(0,g.jsx)(g.Fragment,{})}function O(){var e=(0,i.yj)(d.WF),n=(0,x.Z)(e,2)[1],t=decodeURIComponent((null===n||void 0===n?void 0:n.tableName)||"");(0,N.mq)({eventName:N.FP.PAGE_VIEW,eventProperties:{type:N.ll,page:"table-details-page"}});var s=E.n.getState(),l=s.tableColumnsOnly,a=void 0===l?[]:l,r=s.rawData.base,o=a.find((function(e){return(0,x.Z)(e,1)[0]===t})),u=null===r||void 0===r?void 0:r.tables[t];return t&&u&&o?(0,g.jsxs)(g.Fragment,{children:[(0,g.jsx)(k.Q,{title:u.name,subtitle:"Table",infoTip:u.description,mb:5}),(0,g.jsxs)(c.rj,{width:"100%",templateColumns:{base:"1fr","2xl":"1fr 1px 1fr"},gap:5,children:[(0,g.jsxs)(c.gC,{spacing:10,children:[(0,g.jsxs)(c.xu,{width:"100%",children:[(0,g.jsx)(c.xv,{fontSize:"xl",children:"Table Statistics"}),(0,g.jsx)(c.iz,{my:1}),(0,g.jsx)(N.Se,{tableDatum:u})]}),(0,g.jsxs)(c.xu,{width:"100%",children:[(0,g.jsx)(c.xv,{fontSize:"xl",children:"Duplicate Rows"}),(0,g.jsx)(c.iz,{my:1}),(0,g.jsx)(N.e0,{tableDatum:u})]})]}),(0,g.jsx)(c.iz,{orientation:"vertical"}),(0,g.jsx)(N.rH,{baseTableEntryDatum:null===o||void 0===o?void 0:o[1].base,singleOnly:!0})]})]}):(0,g.jsx)(D.J,{text:"No profile data found for '".concat(t,"'")})}var _=t(2175),I=t(3660),Z=t(5939),q=t(4236),G=t(1352),M=t(5282),R=t(4109);function V(){var e,n,t=(0,I.qY)(),i=(0,j.useState)(-1),s=(0,x.Z)(i,2),l=s[0],a=s[1],r=E.n.getState(),o=r.tableColumnsOnly,d=void 0===o?[]:o,u=r.assertionsOnly;return(0,G.m)({eventName:M.FP.PAGE_VIEW,eventProperties:{type:M.ll,page:"table-list-page"}}),(0,g.jsxs)(g.Fragment,{children:[(0,g.jsx)(c.xv,{fontSize:"xl",fontWeight:"semibold",textAlign:"left",children:"Tables"}),(0,g.jsxs)(c.kC,{direction:"column",width:"100%",minHeight:"650px",children:[(0,g.jsxs)(c.rj,{templateColumns:f.Dp,maxW:f.xD,px:4,my:6,children:[(0,g.jsx)(c.xv,{children:"Name"}),(0,g.jsx)(c.xv,{children:"Summary"}),(0,g.jsx)(c.xv,{children:"Assertions"})]}),d.map((function(e,n){return(0,g.jsx)(Z.h,{combinedAssertions:u,combinedTableEntry:e,singleOnly:!0,onInfoClick:function(){a(n),t.onOpen()}},n)}))]}),(0,g.jsxs)(R.W,(0,_.Z)((0,_.Z)({},t),{},{size:"2xl",title:-1!==l&&d[l][0],onClose:function(){a(-1),t.onClose()},children:[(0,g.jsxs)(c.xv,{fontSize:"lg",mb:4,children:["Description:"," ",null!==(e=-1!==l&&(null===(n=d[l][1].base)||void 0===n?void 0:n.description))&&void 0!==e?e:(0,g.jsx)(c.xv,{as:"i",children:"No description provided."})]}),-1!==l&&(0,g.jsx)(q.r,{singleOnly:!0,baseTableEntryDatum:d[l][1].base})]}))]})}function U(e){var n=e.data,t=e.sideNavTop,x=void 0===t?"0px":t;return(0,o.nq)((function(e){return e.setReportRawData}))({base:n}),(0,g.jsx)(i.F0,{hook:r.w,children:(0,g.jsx)(l.$,{sideNavTop:x,children:(0,g.jsxs)(i.rs,{children:[(0,g.jsx)(i.AW,{path:d.bw,children:(0,g.jsx)(F,{})}),(0,g.jsx)(i.AW,{path:d.KX,children:(0,g.jsx)(V,{})}),(0,g.jsx)(i.AW,{path:d.WF,children:(0,g.jsx)(O,{})}),(0,g.jsx)(i.AW,{path:d.t3,children:(0,g.jsx)(T,{})}),(0,g.jsx)(i.AW,{path:d.$n,children:(0,g.jsx)(y,{})}),(0,g.jsx)(i.AW,{path:d.cs,children:(0,g.jsx)(w,{})}),(0,g.jsx)(i.AW,{path:d.Mu,children:(0,g.jsx)(s.gb,{})}),(0,g.jsx)(i.AW,{children:(0,g.jsx)(a.T,{})})]})})})}var H=U}}]);
//# sourceMappingURL=982.0cd4726a.chunk.js.map