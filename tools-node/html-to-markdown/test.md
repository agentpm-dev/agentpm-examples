AgentPM™ – Agent Package Manager

[

AgentPM™](/)agentpackagemanager.com

AllToolsNamespaces

/

[Docs](/docs/latest/getting-started/introduction#dt)[Pricing](/pricing)[Publish](/docs/latest/publish-a-tool/init#doc-article)[Sign in](/signIn)

1.  [Tools](/explore?type=tools)
2.  /[@zack](/namespaces/e6363bd8-e70c-4c11-928b-ebee22de7ede)
3.  /[http-fetch](#)

## @zack/http-fetch

v0.1.0

Make HTTP requests (GET/POST/etc.) and return normalized response metadata and content.

Install

```
agentpm install @zack/http-fetch@0.1.0
```

Load

NodePython

```
import { load } from '@agentpm/sdk';
const t = await load('@zack/http-fetch@0.1.0');
```

```
from agentpm import load
t = load("@zack/http-fetch@0.1.0")
```

Weekly downloads

0

0%

Last publish

1d ago

v0.1.0

[Overview](/tools/af5f8bac-47b6-44f8-878e-171c6e842392/v0.1.0/overview)[Readme](/tools/af5f8bac-47b6-44f8-878e-171c6e842392/v0.1.0/readme)[Security](/tools/af5f8bac-47b6-44f8-878e-171c6e842392/v0.1.0/security)[Evaluations](/tools/af5f8bac-47b6-44f8-878e-171c6e842392/v0.1.0/evaluations)

agent.json

{
"name": "http-fetch",
"version": "0.1.0",
"description": "Make HTTP requests (GET/POST/etc.) and return normalized response metadata and content.",
"files": \[
"dist/"
\],
"entrypoint": {
"args": \[
"dist/index.js"
\],
"command": "node",
"timeout\_ms": 60000
},
"environment": {
"vars": {
"HTTP\_FETCH\_PROXY\_URL": {
"required": false,
"description": "Optional HTTP(S) proxy URL to route requests through."
},
"HTTP\_FETCH\_DEFAULT\_USER\_AGENT": {
"required": false,
"description": "Optional default User-Agent header to send when none is provided in inputs."
}
}
},
"inputs": {
"type": "object",
"required": \[
"url"
\],
"properties": {
"url": {
"type": "string",
"format": "uri",
"description": "The URL to request."
},
"body": {
"type": "string",
"description": "Optional request body (for POST/PUT/PATCH, etc.). Sent as-is. For JSON, send a JSON-stringified payload and set Content-Type accordingly."
},
"method": {
"enum": \[
"GET",
"POST",
"PUT",
"DELETE",
"PATCH",
"HEAD",
"OPTIONS"
\],
"type": "string",
"default": "GET",
"description": "HTTP method to use."
},
"headers": {
"type": "object",
"description": "Optional request headers as a simple key/value map.",
"additionalProperties": {
"type": "string"
}
},
"max\_bytes": {
"type": "integer",
"default": 1048576,
"maximum": 5242880,
"minimum": 1,
"description": "Maximum number of bytes to read from the response body. Responses larger than this should be truncated."
},
"timeout\_ms": {
"type": "integer",
"default": 30000,
"maximum": 120000,
"minimum": 1,
"description": "Request timeout in milliseconds."
},
"response\_type": {
"enum": \[
"auto",
"text",
"json",
"bytes"
\],
"type": "string",
"default": "auto",
"description": "Hint for how the response body should be returned."
},
"follow\_redirects": {
"type": "boolean",
"default": true,
"description": "Whether to follow HTTP redirects."
}
},
"additionalProperties": false
},
"outputs": {
"oneOf": \[
{
"type": "object",
"required": \[
"ok",
"status",
"headers"
\],
"properties": {
"ok": {
"const": true
},
"status": {
"type": "integer",
"description": "HTTP status code returned by the server."
},
"headers": {
"type": "object",
"description": "Normalized response headers as a key/value map.",
"additionalProperties": {
"type": "string"
}
},
"body\_json": {
"type": "object",
"description": "Parsed JSON response body when response\_type=json (or auto detects JSON)."
},
"body\_text": {
"type": "string",
"description": "UTF-8 text response body when treatable as text (response\_type=text or auto-detected)."
},
"truncated": {
"type": "boolean",
"description": "True if the response body was truncated due to max\_bytes."
},
"url\_final": {
"type": "string",
"description": "Final URL after redirects (if follow\_redirects is true)."
},
"body\_base64": {
"type": "string",
"description": "Base64-encoded response body for binary responses (response\_type=bytes or auto detects binary)."
},
"status\_text": {
"type": "string",
"description": "HTTP status text, if available."
},
"content\_type": {
"type": "string",
"description": "Content-Type header value, if present."
}
},
"additionalProperties": false
},
{
"type": "object",
"required": \[
"ok",
"error"
\],
"properties": {
"ok": {
"const": false
},
"error": {
"type": "object",
"required": \[
"message"
\],
"properties": {
"code": {
"type": "string",
"description": "Stable machine-readable error code (e.g. INPUT\_INVALID, REQUEST\_FAILED, TIMEOUT, RESPONSE\_TOO\_LARGE)."
},
"details": {
"type": "object",
"description": "Optional structured context about the error (e.g. status code, URL).",
"additionalProperties": true
},
"message": {
"type": "string",
"description": "Human-readable error message."
}
},
"additionalProperties": true
}
},
"additionalProperties": false
}
\]
},
"license": {
"file": "LICENSE",
"spdx": "MIT"
},
"runtime": {
"type": "node",
"version": "20"
}
}

Environment variables

Optional

`HTTP_FETCH_PROXY_URL`

Optional HTTP(S) proxy URL to route requests through.

Copy name

`HTTP_FETCH_DEFAULT_USER_AGENT`

Optional default User-Agent header to send when none is provided in inputs.

Copy name

Compatibility

NodePython

Weekly downloads

0

0%

Last publish

1d ago

v0.1.0

Score & rating

Coming Soon

Maintainers

Z

Zack• Author

© 2025 AgentPM™. Built for developers.

[Status](/status)[Terms](/terms)[Privacy](/privacy)

(self.\_\_next\_f=self.\_\_next\_f||\[\]).push(\[0\])self.\_\_next\_f.push(\[1,"1:\\"$Sreact.fragment\\"\\n3:I\[4507,\[\],\\"\\"\]\\n4:I\[2679,\[\],\\"\\"\]\\n7:I\[3218,\[\],\\"OutletBoundary\\"\]\\n9:I\[8487,\[\],\\"AsyncMetadataOutlet\\"\]\\nb:I\[3218,\[\],\\"ViewportBoundary\\"\]\\nd:I\[3218,\[\],\\"MetadataBoundary\\"\]\\ne:\\"$Sreact.suspense\\"\\n10:I\[6737,\[\],\\"\\"\]\\n11:I\[2122,\[\\"3090\\",\\"static/chunks/3090-fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"8011\\",\\"static/chunks/8011-9df4899bc6feedaa.js\\",\\"3737\\",\\"static/chunks/3737-c1fc4aaa19168be9.js\\",\\"7177\\",\\"static/chunks/app/layout-15e54539f89506e9.js\\"\],\\"ClientClerkProvider\\"\]\\n13:I\[3090,\[\\"3090\\",\\"static/chunks/3090-fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"9869\\",\\"static/chunks/9869-a4d88157bf21afe8.js\\",\\"2088\\",\\"static/chunks/app/tools/%5BtoolId%5D/%5Bversion%5D/layout-d4f6bdac68fcf3ab.js\\"\],\\"\\"\]\\n14:I\[3988,\[\\"3090\\",\\"static/chunks/3090-fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"4407\\",\\"static/chunks/app/tools/%5BtoolId%5D/%5Bversion%5D/overview/page-08ca3a0b72b9b519.js\\"\],\\"default\\"\]\\n18:I\[3948,\[\\"3090\\",\\"static/chunks/3090-fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"4407\\",\\"static/chunks/app/tools/%5BtoolId%5D/%5Bversion%5D/overview/page-08ca3a0b72b9b519.js\\"\],\\"EnvironmentVariableSection\\"\]\\n19:I\[4087,\[\\"3090\\",\\"static/chunks/3090-fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"8011\\",\\"static/chunks/8011-9df4899bc6feedaa.js\\",\\"3737\\",\\"static/chunks/3737-c1fc4aaa19168be9.js\\",\\"7177\\",\\"static/chunks/app/layout-15e54539f89506e9.js\\"\],\\"default\\"\]\\n1a:I\[4445,\[\\"3090\\",\\"static/chunks/3090-fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"8011\\",\\"static/chunks/8011-9df4899bc6feedaa.js\\",\\"3737\\",\\"static/chunks/3737-c1fc4aaa19168be9.js\\",\\"7177\\",\\"static/chunks/app/layout-15e54539f89506e9.js\\"\],\\"default\\"\]\\n1b:I\[9543,\[\],\\"IconMark\\"\]\\n1c:I\[6345,\[\\"3090\\",\\"static/chunks/3090-fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"9869\\",\\"static/chunks/9869-a4d88157bf21afe8.js\\",\\"2088\\",\\"static/chunks/app/tools/%5BtoolId%5D/%5Bversion%5D/layout-d4f6bdac68fcf3ab.js\\"\],\\"default\\"\]\\n21:I\[5631,\[\\"3090\\",\\"static/chunks/3090-"\])self.\_\_next\_f.push(\[1,"fc80e85512d34386.js\\",\\"9641\\",\\"static/chunks/9641-c8e27a3fb5a16a82.js\\",\\"9869\\",\\"static/chunks/9869-a4d88157bf21afe8.js\\",\\"2088\\",\\"static/chunks/app/tools/%5BtoolId%5D/%5Bversion%5D/layout-d4f6bdac68fcf3ab.js\\"\],\\"default\\"\]\\n:HL\[\\"/\_next/static/media/e4af272ccee01ff0-s.p.woff2\\",\\"font\\",{\\"crossOrigin\\":\\"\\",\\"type\\":\\"font/woff2\\"}\]\\n:HL\[\\"/\_next/static/css/46fe4a983aba003d.css\\",\\"style\\"\]\\n"\])self.\_\_next\_f.push(\[1,"0:{\\"P\\":null,\\"b\\":\\"8aykKGE-An5KI5tqgr8KC\\",\\"p\\":\\"\\",\\"c\\":\[\\"\\",\\"tools\\",\\"af5f8bac-47b6-44f8-878e-171c6e842392\\",\\"v0.1.0\\",\\"overview\\"\],\\"i\\":false,\\"f\\":\[\[\[\\"\\",{\\"children\\":\[\\"tools\\",{\\"children\\":\[\[\\"toolId\\",\\"af5f8bac-47b6-44f8-878e-171c6e842392\\",\\"d\\"\],{\\"children\\":\[\[\\"version\\",\\"v0.1.0\\",\\"d\\"\],{\\"children\\":\[\\"overview\\",{\\"children\\":\[\\"\_\_PAGE\_\_\\",{}\]}\]}\]}\]}\]},\\"$undefined\\",\\"$undefined\\",true\],\[\\"\\",\[\\"$\\",\\"$1\\",\\"c\\",{\\"children\\":\[\[\[\\"$\\",\\"link\\",\\"0\\",{\\"rel\\":\\"stylesheet\\",\\"href\\":\\"/\_next/static/css/46fe4a983aba003d.css\\",\\"precedence\\":\\"next\\",\\"crossOrigin\\":\\"$undefined\\",\\"nonce\\":\\"$undefined\\"}\]\],\\"$L2\\"\]}\],{\\"children\\":\[\\"tools\\",\[\\"$\\",\\"$1\\",\\"c\\",{\\"children\\":\[null,\[\\"$\\",\\"$L3\\",null,{\\"parallelRouterKey\\":\\"children\\",\\"error\\":\\"$undefined\\",\\"errorStyles\\":\\"$undefined\\",\\"errorScripts\\":\\"$undefined\\",\\"template\\":\[\\"$\\",\\"$L4\\",null,{}\],\\"templateStyles\\":\\"$undefined\\",\\"templateScripts\\":\\"$undefined\\",\\"notFound\\":\\"$undefined\\",\\"forbidden\\":\\"$undefined\\",\\"unauthorized\\":\\"$undefined\\"}\]\]}\],{\\"children\\":\[\[\\"toolId\\",\\"af5f8bac-47b6-44f8-878e-171c6e842392\\",\\"d\\"\],\[\\"$\\",\\"$1\\",\\"c\\",{\\"children\\":\[null,\[\\"$\\",\\"$L3\\",null,{\\"parallelRouterKey\\":\\"children\\",\\"error\\":\\"$undefined\\",\\"errorStyles\\":\\"$undefined\\",\\"errorScripts\\":\\"$undefined\\",\\"template\\":\[\\"$\\",\\"$L4\\",null,{}\],\\"templateStyles\\":\\"$undefined\\",\\"templateScripts\\":\\"$undefined\\",\\"notFound\\":\\"$undefined\\",\\"forbidden\\":\\"$undefined\\",\\"unauthorized\\":\\"$undefined\\"}\]\]}\],{\\"children\\":\[\[\\"version\\",\\"v0.1.0\\",\\"d\\"\],\[\\"$\\",\\"$1\\",\\"c\\",{\\"children\\":\[null,\\"$L5\\"\]}\],{\\"children\\":\[\\"overview\\",\[\\"$\\",\\"$1\\",\\"c\\",{\\"children\\":\[null,\[\\"$\\",\\"$L3\\",null,{\\"parallelRouterKey\\":\\"children\\",\\"error\\":\\"$undefined\\",\\"errorStyles\\":\\"$undefined\\",\\"errorScripts\\":\\"$undefined\\",\\"template\\":\[\\"$\\",\\"$L4\\",null,{}\],\\"templateStyles\\":\\"$undefined\\",\\"templateScripts\\":\\"$undefined\\",\\"notFound\\":\\"$undefined\\",\\"forbidden\\":\\"$undefined\\",\\"unauthorized\\":\\"$undefined\\"}\]\]}\],{\\"children\\":\[\\"\_\_PAGE\_\_\\",\[\\"$\\",\\"$1\\",\\"c\\",{\\"children\\":\[\\"$L6\\",null,\[\\"$\\",\\"$L7\\",null,{\\"children\\":\[\\"$L8\\",\[\\"$\\",\\"$L9\\",null,{\\"promise\\":\\"$@a\\"}\]\]}\]\]}\],{},null,false\]},null,false\]},null,false\]},null,false\]},null,false\]},null,false\],\[\\"$\\",\\"$1\\",\\"h\\",{\\"children\\":\[null,\[\[\\"$\\",\\"$Lb\\",null,{\\"children\\":\\"$Lc\\"}\],\[\\"$\\",\\"meta\\",null,{\\"name\\":\\"next-size-adjust\\",\\"content\\":\\"\\"}\]\],\[\\"$\\",\\"$Ld\\",null,{\\"children\\":\[\\"$\\",\\"div\\",null,{\\"hidden\\":true,\\"children\\":\[\\"$\\",\\"$e\\",null,{\\"fallback\\":null,\\"children\\":\\"$Lf\\"}\]}\]}\]\]}\],false\]\],\\"m\\":\\"$undefined\\",\\"G\\":\[\\"$10\\",\[\]\],\\"s\\":false,\\"S\\":false}\\n"\])self.\_\_next\_f.push(\[1,"2:\[\\"$\\",\\"$L11\\",null,{\\"publishableKey\\":\\"pk\_live\_Y2xlcmsuYWdlbnRwYWNrYWdlbWFuYWdlci5jb20k\\",\\"clerkJSUrl\\":\\"$undefined\\",\\"clerkJSVersion\\":\\"$undefined\\",\\"proxyUrl\\":\\"\\",\\"domain\\":\\"\\",\\"isSatellite\\":false,\\"signInUrl\\":\\"/signIn\\",\\"signUpUrl\\":\\"/signUp\\",\\"signInForceRedirectUrl\\":\\"\\",\\"signUpForceRedirectUrl\\":\\"\\",\\"signInFallbackRedirectUrl\\":\\"\\",\\"signUpFallbackRedirectUrl\\":\\"\\",\\"afterSignInUrl\\":\\"\\",\\"afterSignUpUrl\\":\\"\\",\\"newSubscriptionRedirectUrl\\":\\"\\",\\"telemetry\\":{\\"disabled\\":false,\\"debug\\":false},\\"sdkMetadata\\":{\\"name\\":\\"@clerk/nextjs\\",\\"version\\":\\"6.33.2\\",\\"environment\\":\\"production\\"},\\"nonce\\":\\"\\",\\"initialState\\":null,\\"children\\":\[\\"$\\",\\"html\\",null,{\\"lang\\":\\"en\\",\\"className\\":\\"\_\_variable\_f367f3 h-full\\",\\"children\\":\[\\"$\\",\\"body\\",null,{\\"children\\":\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-h-screen bg-slate-950 text-slate-100 antialiased\\",\\"children\\":\[\\"$L12\\",\[\\"$\\",\\"main\\",null,{\\"className\\":\\"max-w-7xl mx-auto px-4\\",\\"children\\":\[\[\\"$\\",\\"$L3\\",null,{\\"parallelRouterKey\\":\\"children\\",\\"error\\":\\"$undefined\\",\\"errorStyles\\":\\"$undefined\\",\\"errorScripts\\":\\"$undefined\\",\\"template\\":\[\\"$\\",\\"$L4\\",null,{}\],\\"templateStyles\\":\\"$undefined\\",\\"templateScripts\\":\\"$undefined\\",\\"notFound\\":\[\[\[\\"$\\",\\"title\\",null,{\\"children\\":\\"404: This page could not be found.\\"}\],\[\\"$\\",\\"div\\",null,{\\"style\\":{\\"fontFamily\\":\\"system-ui,\\\\\\"Segoe UI\\\\\\",Roboto,Helvetica,Arial,sans-serif,\\\\\\"Apple Color Emoji\\\\\\",\\\\\\"Segoe UI Emoji\\\\\\"\\",\\"height\\":\\"100vh\\",\\"textAlign\\":\\"center\\",\\"display\\":\\"flex\\",\\"flexDirection\\":\\"column\\",\\"alignItems\\":\\"center\\",\\"justifyContent\\":\\"center\\"},\\"children\\":\[\\"$\\",\\"div\\",null,{\\"children\\":\[\[\\"$\\",\\"style\\",null,{\\"dangerouslySetInnerHTML\\":{\\"\_\_html\\":\\"body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}\\"}}\],\[\\"$\\",\\"h1\\",null,{\\"className\\":\\"next-error-h1\\",\\"style\\":{\\"display\\":\\"inline-block\\",\\"margin\\":\\"0 20px 0 0\\",\\"padding\\":\\"0 23px 0 0\\",\\"fontSize\\":24,\\"fontWeight\\":500,\\"verticalAlign\\":\\"top\\",\\"lineHeight\\":\\"49px\\"},\\"children\\":404}\],\[\\"$\\",\\"div\\",null,{\\"style\\":{\\"display\\":\\"inline-block\\"},\\"children\\":\[\\"$\\",\\"h2\\",null,{\\"style\\":{\\"fontSize\\":14,\\"fontWeight\\":400,\\"lineHeight\\":\\"49px\\",\\"margin\\":0},\\"children\\":\\"This page could not be found.\\"}\]}\]\]}\]}\]\],\[\]\],\\"forbidden\\":\\"$undefined\\",\\"unauthorized\\":\\"$undefined\\"}\],\[\\"$\\",\\"footer\\",null,{\\"className\\":\\"py-10 text-sm text-slate-400 border-t border-slate-800 mt-10\\",\\"children\\":\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex flex-col sm:flex-row items-center justify-between gap-4\\",\\"children\\":\[\[\\"$\\",\\"p\\",null,{\\"children\\":\[\\"© \\",2025,\\" AgentPM™. Built for developers.\\"\]}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex items-center gap-4\\",\\"children\\":\[\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/status\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-400 hover:text-slate-200\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Status\\"}\],\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/terms\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-400 hover:text-slate-200\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Terms\\"}\],\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/privacy\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-400 hover:text-slate-200\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Privacy\\"}\]\]}\]\]}\]}\]\]}\]\]}\]}\]}\]}\]\\n"\])self.\_\_next\_f.push(\[1,"15:T153b,"\])self.\_\_next\_f.push(\[1,"{\\n \\"name\\": \\"http-fetch\\",\\n \\"version\\": \\"0.1.0\\",\\n \\"description\\": \\"Make HTTP requests (GET/POST/etc.) and return normalized response metadata and content.\\",\\n \\"files\\": \[\\n \\"dist/\\"\\n \],\\n \\"entrypoint\\": {\\n \\"args\\": \[\\n \\"dist/index.js\\"\\n \],\\n \\"command\\": \\"node\\",\\n \\"timeout\_ms\\": 60000\\n },\\n \\"environment\\": {\\n \\"vars\\": {\\n \\"HTTP\_FETCH\_PROXY\_URL\\": {\\n \\"required\\": false,\\n \\"description\\": \\"Optional HTTP(S) proxy URL to route requests through.\\"\\n },\\n \\"HTTP\_FETCH\_DEFAULT\_USER\_AGENT\\": {\\n \\"required\\": false,\\n \\"description\\": \\"Optional default User-Agent header to send when none is provided in inputs.\\"\\n }\\n }\\n },\\n \\"inputs\\": {\\n \\"type\\": \\"object\\",\\n \\"required\\": \[\\n \\"url\\"\\n \],\\n \\"properties\\": {\\n \\"url\\": {\\n \\"type\\": \\"string\\",\\n \\"format\\": \\"uri\\",\\n \\"description\\": \\"The URL to request.\\"\\n },\\n \\"body\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"Optional request body (for POST/PUT/PATCH, etc.). Sent as-is. For JSON, send a JSON-stringified payload and set Content-Type accordingly.\\"\\n },\\n \\"method\\": {\\n \\"enum\\": \[\\n \\"GET\\",\\n \\"POST\\",\\n \\"PUT\\",\\n \\"DELETE\\",\\n \\"PATCH\\",\\n \\"HEAD\\",\\n \\"OPTIONS\\"\\n \],\\n \\"type\\": \\"string\\",\\n \\"default\\": \\"GET\\",\\n \\"description\\": \\"HTTP method to use.\\"\\n },\\n \\"headers\\": {\\n \\"type\\": \\"object\\",\\n \\"description\\": \\"Optional request headers as a simple key/value map.\\",\\n \\"additionalProperties\\": {\\n \\"type\\": \\"string\\"\\n }\\n },\\n \\"max\_bytes\\": {\\n \\"type\\": \\"integer\\",\\n \\"default\\": 1048576,\\n \\"maximum\\": 5242880,\\n \\"minimum\\": 1,\\n \\"description\\": \\"Maximum number of bytes to read from the response body. Responses larger than this should be truncated.\\"\\n },\\n \\"timeout\_ms\\": {\\n \\"type\\": \\"integer\\",\\n \\"default\\": 30000,\\n \\"maximum\\": 120000,\\n \\"minimum\\": 1,\\n \\"description\\": \\"Request timeout in milliseconds.\\"\\n },\\n \\"response\_type\\": {\\n \\"enum\\": \[\\n \\"auto\\",\\n \\"text\\",\\n \\"json\\",\\n \\"bytes\\"\\n \],\\n \\"type\\": \\"string\\",\\n \\"default\\": \\"auto\\",\\n \\"description\\": \\"Hint for how the response body should be returned.\\"\\n },\\n \\"follow\_redirects\\": {\\n \\"type\\": \\"boolean\\",\\n \\"default\\": true,\\n \\"description\\": \\"Whether to follow HTTP redirects.\\"\\n }\\n },\\n \\"additionalProperties\\": false\\n },\\n \\"outputs\\": {\\n \\"oneOf\\": \[\\n {\\n \\"type\\": \\"object\\",\\n \\"required\\": \[\\n \\"ok\\",\\n \\"status\\",\\n \\"headers\\"\\n \],\\n \\"properties\\": {\\n \\"ok\\": {\\n \\"const\\": true\\n },\\n \\"status\\": {\\n \\"type\\": \\"integer\\",\\n \\"description\\": \\"HTTP status code returned by the server.\\"\\n },\\n \\"headers\\": {\\n \\"type\\": \\"object\\",\\n \\"description\\": \\"Normalized response headers as a key/value map.\\",\\n \\"additionalProperties\\": {\\n \\"type\\": \\"string\\"\\n }\\n },\\n \\"body\_json\\": {\\n \\"type\\": \\"object\\",\\n \\"description\\": \\"Parsed JSON response body when response\_type=json (or auto detects JSON).\\"\\n },\\n \\"body\_text\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"UTF-8 text response body when treatable as text (response\_type=text or auto-detected).\\"\\n },\\n \\"truncated\\": {\\n \\"type\\": \\"boolean\\",\\n \\"description\\": \\"True if the response body was truncated due to max\_bytes.\\"\\n },\\n \\"url\_final\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"Final URL after redirects (if follow\_redirects is true).\\"\\n },\\n \\"body\_base64\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"Base64-encoded response body for binary responses (response\_type=bytes or auto detects binary).\\"\\n },\\n \\"status\_text\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"HTTP status text, if available.\\"\\n },\\n \\"content\_type\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"Content-Type header value, if present.\\"\\n }\\n },\\n \\"additionalProperties\\": false\\n },\\n {\\n \\"type\\": \\"object\\",\\n \\"required\\": \[\\n \\"ok\\",\\n \\"error\\"\\n \],\\n \\"properties\\": {\\n \\"ok\\": {\\n \\"const\\": false\\n },\\n \\"error\\": {\\n \\"type\\": \\"object\\",\\n \\"required\\": \[\\n \\"message\\"\\n \],\\n \\"properties\\": {\\n \\"code\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"Stable machine-readable error code (e.g. INPUT\_INVALID, REQUEST\_FAILED, TIMEOUT, RESPONSE\_TOO\_LARGE).\\"\\n },\\n \\"details\\": {\\n \\"type\\": \\"object\\",\\n \\"description\\": \\"Optional structured context about the error (e.g. status code, URL).\\",\\n \\"additionalProperties\\": true\\n },\\n \\"message\\": {\\n \\"type\\": \\"string\\",\\n \\"description\\": \\"Human-readable error message.\\"\\n }\\n },\\n \\"additionalProperties\\": true\\n }\\n },\\n \\"additionalProperties\\": false\\n }\\n \]\\n },\\n \\"license\\": {\\n \\"file\\": \\"LICENSE\\",\\n \\"spdx\\": \\"MIT\\"\\n },\\n \\"runtime\\": {\\n \\"type\\": \\"node\\",\\n \\"version\\": \\"20\\"\\n }\\n}"\])self.\_\_next\_f.push(\[1,"6:\[\[\\"$\\",\\"$L14\\",null,{\\"title\\":\\"agent.json\\",\\"children\\":\[\\"$\\",\\"pre\\",null,{\\"className\\":\\"text-xs bg-slate-950/60 border border-slate-800 rounded-xl p-3 overflow-auto\\",\\"children\\":\\"$15\\"}\]}\],\\"$L16\\",\\"$L17\\"\]\\n"\])self.\_\_next\_f.push(\[1,"16:\[\\"$\\",\\"$L14\\",null,{\\"title\\":\\"Environment variables\\",\\"children\\":\[\\"$\\",\\"div\\",null,{\\"className\\":\\"space-y-3 text-sm\\",\\"children\\":\[false,\[\\"$\\",\\"div\\",null,{\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xs text-slate-400 mb-1\\",\\"children\\":\\"Optional\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex flex-col gap-2\\",\\"children\\":\[\[\\"$\\",\\"$L18\\",\\"HTTP\_FETCH\_PROXY\_URL\\",{\\"variable\\":\\"HTTP\_FETCH\_PROXY\_URL\\",\\"value\\":{\\"required\\":false,\\"description\\":\\"Optional HTTP(S) proxy URL to route requests through.\\"}}\],\[\\"$\\",\\"$L18\\",\\"HTTP\_FETCH\_DEFAULT\_USER\_AGENT\\",{\\"variable\\":\\"HTTP\_FETCH\_DEFAULT\_USER\_AGENT\\",\\"value\\":{\\"required\\":false,\\"description\\":\\"Optional default User-Agent header to send when none is provided in inputs.\\"}}\]\]}\]\]}\]\]}\]}\]\\n"\])self.\_\_next\_f.push(\[1,"17:\[\\"$\\",\\"$L14\\",null,{\\"title\\":\\"Compatibility\\",\\"children\\":\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex flex-wrap gap-2 text-xs\\",\\"children\\":\[\[\\"$\\",\\"span\\",null,{\\"className\\":\\"text-\[10px\] px-2 py-0.5 rounded-full border bg-slate-500/10 text-slate-300 border-slate-700/50\\",\\"children\\":\\"Node\\"}\],\[\\"$\\",\\"span\\",null,{\\"className\\":\\"text-\[10px\] px-2 py-0.5 rounded-full border bg-slate-500/10 text-slate-300 border-slate-700/50\\",\\"children\\":\\"Python\\"}\]\]}\]}\]\\n"\])self.\_\_next\_f.push(\[1,"12:\[\\"$\\",\\"header\\",null,{\\"className\\":\\"sticky top-0 z-40 backdrop-blur bg-slate-950/70 border-b border-slate-800\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"max-w-7xl mx-auto px-4 py-3 flex items-center gap-3\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex items-center gap-2\\",\\"children\\":\[\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/\\",\\"className\\":\\"flex items-center gap-2\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"h-8 w-8 rounded-xl bg-gradient-to-br from-sky-500 to-fuchsia-500\\"}\],\[\\"$\\",\\"span\\",null,{\\"className\\":\\"font-semibold tracking-tight\\",\\"children\\":\\"AgentPM™\\"}\]\]}\],\[\\"$\\",\\"span\\",null,{\\"className\\":\\"ml-2 text-xs text-slate-400 hidden lg:inline\\",\\"children\\":\\"agentpackagemanager.com\\"}\]\]}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex-1\\"}\],\[\\"$\\",\\"$L19\\",null,{\\"initial\\":{\\"type\\":\\"all\\",\\"q\\":\\"\\"}}\],\[\\"$\\",\\"nav\\",null,{\\"className\\":\\"flex items-center gap-3 text-sm\\",\\"children\\":\[\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/docs/latest/getting-started/introduction#dt\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-300 hover:text-white\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Docs\\"}\],\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/pricing\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-300 hover:text-white\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Pricing\\"}\],\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/docs/latest/publish-a-tool/init#doc-article\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-300 hover:text-white\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Publish\\"}\],\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/signIn\\",\\"className\\":\\"whitespace-nowrap transition-colors text-sky-400 hover:text-sky-300\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Sign in\\"}\]\]}\]\]}\],\[\\"$\\",\\"$L1a\\",null,{}\]\]}\]\\n"\])self.\_\_next\_f.push(\[1,"c:\[\[\\"$\\",\\"meta\\",\\"0\\",{\\"charSet\\":\\"utf-8\\"}\],\[\\"$\\",\\"meta\\",\\"1\\",{\\"name\\":\\"viewport\\",\\"content\\":\\"width=device-width, initial-scale=1\\"}\],\[\\"$\\",\\"meta\\",\\"2\\",{\\"name\\":\\"theme-color\\",\\"media\\":\\"(prefers-color-scheme: light)\\",\\"content\\":\\"#ffffff\\"}\],\[\\"$\\",\\"meta\\",\\"3\\",{\\"name\\":\\"theme-color\\",\\"media\\":\\"(prefers-color-scheme: dark)\\",\\"content\\":\\"#0b1220\\"}\],\[\\"$\\",\\"meta\\",\\"4\\",{\\"name\\":\\"color-scheme\\",\\"content\\":\\"light dark\\"}\]\]\\n8:null\\n"\])self.\_\_next\_f.push(\[1,"a:{\\"metadata\\":\[\[\\"$\\",\\"title\\",\\"0\\",{\\"children\\":\\"AgentPM™ – Agent Package Manager\\"}\],\[\\"$\\",\\"meta\\",\\"1\\",{\\"name\\":\\"description\\",\\"content\\":\\"Discover, verify, and integrate reusable tools for AI agents. AgentPM™ is the package manager for agent tooling.\\"}\],\[\\"$\\",\\"meta\\",\\"2\\",{\\"name\\":\\"application-name\\",\\"content\\":\\"AgentPM\\"}\],\[\\"$\\",\\"meta\\",\\"3\\",{\\"name\\":\\"author\\",\\"content\\":\\"AgentPM\\"}\],\[\\"$\\",\\"link\\",\\"4\\",{\\"rel\\":\\"manifest\\",\\"href\\":\\"/site.webmanifest\\",\\"crossOrigin\\":\\"$undefined\\"}\],\[\\"$\\",\\"meta\\",\\"5\\",{\\"name\\":\\"keywords\\",\\"content\\":\\"AgentPM,Agent Package Manager,AI tools,agents,tool registry,LLM,SDK\\"}\],\[\\"$\\",\\"meta\\",\\"6\\",{\\"name\\":\\"creator\\",\\"content\\":\\"AgentPM\\"}\],\[\\"$\\",\\"meta\\",\\"7\\",{\\"name\\":\\"publisher\\",\\"content\\":\\"AgentPM\\"}\],\[\\"$\\",\\"meta\\",\\"8\\",{\\"name\\":\\"robots\\",\\"content\\":\\"index, follow\\"}\],\[\\"$\\",\\"meta\\",\\"9\\",{\\"name\\":\\"googlebot\\",\\"content\\":\\"index, follow, max-video-preview:-1, max-image-preview:large, max-snippet:-1\\"}\],\[\\"$\\",\\"meta\\",\\"10\\",{\\"name\\":\\"category\\",\\"content\\":\\"technology\\"}\],\[\\"$\\",\\"link\\",\\"11\\",{\\"rel\\":\\"canonical\\",\\"href\\":\\"https://agentpackagemanager.com\\"}\],\[\\"$\\",\\"link\\",\\"12\\",{\\"rel\\":\\"alternate\\",\\"hrefLang\\":\\"en-US\\",\\"href\\":\\"https://agentpackagemanager.com\\"}\],\[\\"$\\",\\"meta\\",\\"13\\",{\\"property\\":\\"og:title\\",\\"content\\":\\"AgentPM™ – Agent Package Manager\\"}\],\[\\"$\\",\\"meta\\",\\"14\\",{\\"property\\":\\"og:description\\",\\"content\\":\\"Discover, verify, and integrate reusable tools for AI agents. AgentPM™ is the package manager for agent tooling.\\"}\],\[\\"$\\",\\"meta\\",\\"15\\",{\\"property\\":\\"og:url\\",\\"content\\":\\"https://agentpackagemanager.com\\"}\],\[\\"$\\",\\"meta\\",\\"16\\",{\\"property\\":\\"og:site\_name\\",\\"content\\":\\"AgentPM\\"}\],\[\\"$\\",\\"meta\\",\\"17\\",{\\"property\\":\\"og:image\\",\\"content\\":\\"https://agentpackagemanager.com/og.png\\"}\],\[\\"$\\",\\"meta\\",\\"18\\",{\\"property\\":\\"og:image:width\\",\\"content\\":\\"1200\\"}\],\[\\"$\\",\\"meta\\",\\"19\\",{\\"property\\":\\"og:image:height\\",\\"content\\":\\"630\\"}\],\[\\"$\\",\\"meta\\",\\"20\\",{\\"property\\":\\"og:image:alt\\",\\"content\\":\\"AgentPM\\"}\],\[\\"$\\",\\"meta\\",\\"21\\",{\\"property\\":\\"og:type\\",\\"content\\":\\"website\\"}\],\[\\"$\\",\\"meta\\",\\"22\\",{\\"name\\":\\"twitter:card\\",\\"content\\":\\"summary\_large\_image\\"}\],\[\\"$\\",\\"meta\\",\\"23\\",{\\"name\\":\\"twitter:title\\",\\"content\\":\\"AgentPM™ – Agent Package Manager\\"}\],\[\\"$\\",\\"meta\\",\\"24\\",{\\"name\\":\\"twitter:description\\",\\"content\\":\\"Discover, verify, and integrate reusable tools for AI agents. AgentPM™ is the package manager for agent tooling.\\"}\],\[\\"$\\",\\"meta\\",\\"25\\",{\\"name\\":\\"twitter:image\\",\\"content\\":\\"https://agentpackagemanager.com/og.png\\"}\],\[\\"$\\",\\"link\\",\\"26\\",{\\"rel\\":\\"icon\\",\\"href\\":\\"/favicon.ico\\"}\],\[\\"$\\",\\"link\\",\\"27\\",{\\"rel\\":\\"icon\\",\\"href\\":\\"/icon-192.png\\",\\"sizes\\":\\"192x192\\",\\"type\\":\\"image/png\\"}\],\[\\"$\\",\\"link\\",\\"28\\",{\\"rel\\":\\"icon\\",\\"href\\":\\"/icon-512.png\\",\\"sizes\\":\\"512x512\\",\\"type\\":\\"image/png\\"}\],\[\\"$\\",\\"link\\",\\"29\\",{\\"rel\\":\\"apple-touch-icon\\",\\"href\\":\\"/apple-touch-icon.png\\",\\"sizes\\":\\"180x180\\"}\],\[\\"$\\",\\"link\\",\\"30\\",{\\"rel\\":\\"mask-icon\\",\\"href\\":\\"/safari-pinned-tab.svg\\",\\"color\\":\\"#5bbad5\\"}\],\[\\"$\\",\\"$L1b\\",\\"31\\",{}\]\],\\"error\\":null,\\"digest\\":\\"$undefined\\"}\\n"\])self.\_\_next\_f.push(\[1,"f:\\"$a:metadata\\"\\n"\])self.\_\_next\_f.push(\[1,"5:\[\\"$\\",\\"section\\",null,{\\"className\\":\\"py-10 sm:py-16 scroll-m-28\\",\\"id\\":\\"t\\",\\"children\\":\[\[\\"$\\",\\"nav\\",null,{\\"className\\":\\"text-sm text-slate-400\\",\\"aria-label\\":\\"Breadcrumb\\",\\"children\\":\[\\"$\\",\\"ol\\",null,{\\"className\\":\\"flex items-center gap-2\\",\\"children\\":\[\[\\"$\\",\\"li\\",\\"0\\",{\\"className\\":\\"flex items-center gap-2\\",\\"children\\":\[false,\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/explore?type=tools\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-300 hover:text-slate-200\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"Tools\\"}\]\]}\],\[\\"$\\",\\"li\\",\\"1\\",{\\"className\\":\\"flex items-center gap-2\\",\\"children\\":\[\[\\"$\\",\\"span\\",null,{\\"className\\":\\"text-slate-600\\",\\"children\\":\\"/\\"}\],\[\\"$\\",\\"$L13\\",null,{\\"href\\":\\"/namespaces/e6363bd8-e70c-4c11-928b-ebee22de7ede\\",\\"className\\":\\"whitespace-nowrap transition-colors text-slate-300 hover:text-slate-200\\",\\"prefetch\\":\\"$undefined\\",\\"replace\\":\\"$undefined\\",\\"scroll\\":\\"$undefined\\",\\"shallow\\":\\"$undefined\\",\\"locale\\":\\"$undefined\\",\\"children\\":\\"@zack\\"}\]\]}\],\[\\"$\\",\\"li\\",\\"2\\",{\\"className\\":\\"flex items-center gap-2\\",\\"children\\":\[\[\\"$\\",\\"span\\",null,{\\"className\\":\\"text-slate-600\\",\\"children\\":\\"/\\"}\],\[\\"$\\",\\"a\\",null,{\\"href\\":\\"#\\",\\"className\\":\\"whitespace-nowrap transition-colors hover:text-white text-slate-200\\",\\"children\\":\\"http-fetch\\"}\]\]}\]\]}\]}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"grid lg:grid-cols-12 gap-x-6 mt-4\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 lg:col-span-8 space-y-4\\",\\"children\\":\[\[\\"$\\",\\"header\\",null,{\\"className\\":\\"rounded-2xl border border-slate-800 bg-slate-900/50 p-4\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex gap-3 items-start\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"shrink-0 h-10 w-10 rounded-xl\\",\\"style\\":{\\"background\\":\\"linear-gradient(117deg, hsl(314, 85%, 53%), hsl(36.30521184857935, 72%, 41%))\\"}}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex-1\\",\\"children\\":\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex flex-wrap gap-2\\",\\"children\\":\[\[\\"$\\",\\"h2\\",null,{\\"className\\":\\"font-semibold text-lg break-all\\",\\"children\\":\\"@zack/http-fetch\\"}\],\[\\"$\\",\\"$L1c\\",null,{\\"toolId\\":\\"af5f8bac-47b6-44f8-878e-171c6e842392\\",\\"version\\":\\"v0.1.0\\",\\"toolVersions\\":{\\"versions\\":\[{\\"tool\_version\_id\\":36,\\"version\\":\\"0.1.0\\"}\]}}\]\]}\]}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex flex-wrap items-center gap-2 text-xs\\",\\"children\\":\\"$undefined\\"}\]\]}\],\[\\"$\\",\\"p\\",null,{\\"className\\":\\"ms-12 mt-1.5 sm:mt-0 ps-1 text-slate-400 text-sm\\",\\"children\\":\\"Make HTTP requests (GET/POST/etc.) and return normalized response metadata and content.\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"mt-3 grid sm:grid-cols-2 gap-3\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 rounded-2xl border border-slate-800 bg-slate-950/50 p-4\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"mb-1 text-xs text-slate-400\\",\\"children\\":\\"Install\\"}\],false,false,\[\[\\"$\\",\\"div\\",\\"code-install-tool-opt1\\",{\\"className\\":\\"block peer-checked/opt1:block\\",\\"children\\":\[\\"$\\",\\"pre\\",null,{\\"className\\":\\"w-full max-w-full overflow-auto text-xs\\",\\"children\\":\[\\"$\\",\\"code\\",null,{\\"children\\":\\"agentpm install @zack/http-fetch@0.1.0\\"}\]}\]}\]\]\]}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 rounded-2xl border border-slate-800 bg-slate-950/50 p-4\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"mb-1 text-xs text-slate-400\\",\\"children\\":\\"Load\\"}\],\[\[\\"$\\",\\"input\\",\\"radio-load-tool-opt1\\",{\\"id\\":\\"load-tool-opt1\\",\\"type\\":\\"radio\\",\\"name\\":\\"load-tool\\",\\"className\\":\\"peer/opt1 sr-only\\",\\"defaultChecked\\":true}\],\[\\"$\\",\\"input\\",\\"radio-load-tool-opt2\\",{\\"id\\":\\"load-tool-opt2\\",\\"type\\":\\"radio\\",\\"name\\":\\"load-tool\\",\\"className\\":\\"peer/opt2 sr-only\\",\\"defaultChecked\\":false}\]\],\[\[\\"$\\",\\"label\\",\\"label-load-tool-opt1\\",{\\"htmlFor\\":\\"load-tool-opt1\\",\\"className\\":\\"text-xs mb-2 me-2 inline-block cursor-pointer rounded-lg border border-slate-800 px-2 py-1 hover:border-slate-700 peer-checked/opt1:bg-slate-800 peer-checked/opt1:text-slate-100\\",\\"children\\":\\"Node\\"}\],\[\\"$\\",\\"label\\",\\"label-load-tool-opt2\\",{\\"htmlFor\\":\\"load-tool-opt2\\",\\"className\\":\\"text-xs mb-2 me-2 inline-block cursor-pointer rounded-lg border border-slate-800 px-2 py-1 hover:border-slate-700 peer-checked/opt2:bg-slate-800 peer-checked/opt2:text-slate-100\\",\\"children\\":\\"Python\\"}\]\],\[\[\\"$\\",\\"div\\",\\"code-load-tool-opt1\\",{\\"className\\":\\"hidden peer-checked/opt1:block\\",\\"children\\":\[\\"$\\",\\"pre\\",null,{\\"className\\":\\"w-full max-w-full overflow-auto text-xs\\",\\"children\\":\[\\"$\\",\\"code\\",null,{\\"children\\":\\"import { load } from '@agentpm/sdk';\\\\nconst t = await load('@zack/http-fetch@0.1.0');\\"}\]}\]}\],\[\\"$\\",\\"div\\",\\"code-load-tool-opt2\\",{\\"className\\":\\"hidden peer-checked/opt2:block\\",\\"children\\":\\"$L1d\\"}\]\]\]}\]\]}\]\]}\],\\"$L1e\\",\\"$L1f\\"\]}\],\\"$L20\\"\]}\]\]}\]\\n"\])self.\_\_next\_f.push(\[1,"1d:\[\\"$\\",\\"pre\\",null,{\\"className\\":\\"w-full max-w-full overflow-auto text-xs\\",\\"children\\":\[\\"$\\",\\"code\\",null,{\\"children\\":\\"from agentpm import load\\\\nt = load(\\\\\\"@zack/http-fetch@0.1.0\\\\\\")\\"}\]}\]\\n"\])self.\_\_next\_f.push(\[1,"1e:\[\\"$\\",\\"div\\",null,{\\"className\\":\\"grid lg:hidden sm:grid-cols-2 gap-3 gap-y-4\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 rounded-2xl bg-slate-900 p-4 border border-slate-800\\",\\"style\\":{\\"--tw-bg-opacity\\":0.6,\\"--tw-border-opacity\\":1},\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xs text-slate-400\\",\\"children\\":\\"Weekly downloads\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"mt-1 flex items-baseline gap-2\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xl font-semibold\\",\\"children\\":\\"0\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-\[10px\] \\",\\"children\\":\\" 0%\\"}\]\]}\]\]}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 rounded-2xl bg-slate-900 p-4 border border-slate-800\\",\\"style\\":{\\"--tw-bg-opacity\\":0.6,\\"--tw-border-opacity\\":1},\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xs text-slate-400\\",\\"children\\":\\"Last publish\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"mt-1 flex items-baseline gap-2\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xl font-semibold\\",\\"children\\":\\"1d ago\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-\[10px\] text-emerald-300\\",\\"children\\":\\"v0.1.0\\"}\]\]}\]\]}\]\]}\]\\n"\])self.\_\_next\_f.push(\[1,"1f:\[\\"$\\",\\"div\\",null,{\\"className\\":\\"rounded-2xl border border-slate-800 overflow-hidden\\",\\"children\\":\[\[\\"$\\",\\"$L21\\",null,{\\"toolId\\":\\"af5f8bac-47b6-44f8-878e-171c6e842392\\",\\"version\\":\\"v0.1.0\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"p-4 space-y-4\\",\\"children\\":\[\\"$\\",\\"$L3\\",null,{\\"parallelRouterKey\\":\\"children\\",\\"error\\":\\"$undefined\\",\\"errorStyles\\":\\"$undefined\\",\\"errorScripts\\":\\"$undefined\\",\\"template\\":\[\\"$\\",\\"$L4\\",null,{}\],\\"templateStyles\\":\\"$undefined\\",\\"templateScripts\\":\\"$undefined\\",\\"notFound\\":\\"$undefined\\",\\"forbidden\\":\\"$undefined\\",\\"unauthorized\\":\\"$undefined\\"}\]}\]\]}\]\\n"\])self.\_\_next\_f.push(\[1,"20:\[\\"$\\",\\"aside\\",null,{\\"className\\":\\"lg:col-span-4 space-y-4\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"hidden lg:grid grid-cols-2 gap-3\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 rounded-2xl bg-slate-900 p-4 border border-slate-800\\",\\"style\\":{\\"--tw-bg-opacity\\":0.6,\\"--tw-border-opacity\\":1},\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xs text-slate-400\\",\\"children\\":\\"Weekly downloads\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"mt-1 flex items-baseline gap-2\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xl font-semibold\\",\\"children\\":\\"0\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-\[10px\] \\",\\"children\\":\\" 0%\\"}\]\]}\]\]}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 rounded-2xl bg-slate-900 p-4 border border-slate-800\\",\\"style\\":{\\"--tw-bg-opacity\\":0.6,\\"--tw-border-opacity\\":1},\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xs text-slate-400\\",\\"children\\":\\"Last publish\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"mt-1 flex items-baseline gap-2\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-xl font-semibold\\",\\"children\\":\\"1d ago\\"}\],\[\\"$\\",\\"div\\",null,{\\"className\\":\\"text-\[10px\] text-emerald-300\\",\\"children\\":\\"v0.1.0\\"}\]\]}\]\]}\]\]}\],\[\\"$\\",\\"$L14\\",null,{\\"title\\":\\"Score \\u0026 rating\\",\\"children\\":\[\\"$\\",\\"div\\",null,{\\"className\\":\\"min-w-0 bg-slate-900 p-4 border border-slate-800 h-28 rounded-xl grid place-items-center text-slate-400 text-xs\\",\\"style\\":{\\"--tw-bg-opacity\\":0.6,\\"--tw-border-opacity\\":1},\\"children\\":\\"Coming Soon\\"}\]}\],\[\\"$\\",\\"$L14\\",null,{\\"title\\":\\"Maintainers\\",\\"children\\":\[\\"$\\",\\"div\\",null,{\\"className\\":\\"flex items-center gap-2 text-sm\\",\\"children\\":\[\[\\"$\\",\\"div\\",null,{\\"className\\":\\"h-8 w-8 rounded-full bg-slate-800 grid place-items-center text-slate-200 text-sm font-medium\\",\\"children\\":\\"Z\\"}\],\[\\"$\\",\\"span\\",null,{\\"children\\":\\"Zack\\"}\],\[\\"$\\",\\"span\\",null,{\\"className\\":\\"text-slate-500\\",\\"children\\":\\"• Author\\"}\]\]}\]}\]\]}\]\\n"\])
