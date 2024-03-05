===========================================================
How to improve security for an Azure Static Web App website
===========================================================

:date: 2024-03-03 17:30

:category: Cloud
:tags: Azure, CI/CD, Github, Security, Website
:author: Kevin D. Reid
:slug: azure-static-web-app-security
:url: azure-static-web-app-security
:status: published


It's been a full month since launching this blog. I've uploaded a few articles and have been steadily working on more projects to document for it. However, I had this nagging thought in my head that my work wasn't quite done here. Simply launching a blog isn't enough; I wanted it to have the best security possible. With this article, I'll dive into further improvements that can be made to enhance the security of a website hosted on Azure Static Web Apps.

What's our security standing?
=============================

To improve the security of your site, it's important to know your current security posture. There are a multitude of free analyzers available that can provide a detailed look into different aspects of a website. 

For starters, let's look into the SSL certificate. An SSL certificate contains verification info for the owner of the domain, and is used for encrypting web traffic between the user and the server. Calling it an SSL certificate is a bit of a misnomer as the Secure Sockets Layer protocol has been superseded by Transport Layer Security or TLS, but the name is still commonly used today. For analysis of the certificate on our website, Qualys offers up a free `SSL Server Test`_ which allows you to test the secure connection between your site and its users. Entering a domain name will run a number of tests, with the full report ready within a few minutes.

.. _`SSL Server Test`: https://www.ssllabs.com/ssltest/index.html

.. image:: images/azure-swa-security/ssl-report-before.png
	:alt: Qualys SSL Server test report with grade of "A"

Our initial score is an A, pretty good already for the default config. There are a few areas we can improve on, starting at the top with DNS CAA. `DNS Certificate Authority Authorization`_ is a DNS record that when set, indicates which certificate authorities can supply an SSL certificate for a domain. We don't currently have this set, but will deal with it soon enough.

.. _`DNS Certificate Authority Authorization`: https://letsencrypt.org/docs/caa/

.. image:: images/azure-swa-security/ssl-caa-before.png 
	:alt: SSL Server test showing missing DNS CAA record

Scrolling through the rest of the report, we can see the protocols and ciphers in use, along with a simulation of what security level is negotiated for various device configurations. Moving down to protocol details shows the different security features supported and vulnerabilities mitigated, and it's here where we see another configuration issue.

.. image:: images/azure-swa-security/ssl-hsts-before.png
	:alt: SSL Server test showing incorrect HSTS settings and session resumption issue

As shown above, we have HSTS enabled. `HTTP Strict Transport Security`_ is used to force connections to use HTTPS, preventing downgrade to insecure HTTP. Our problem comes with the max-age being set too low, with the recommendation being 6 months or greater. The session resumption warning in orange is caused by the Azure SWA platform and cannot be fixed, but it's only a minor issue and doesn't impact the score.

.. _`HTTP Strict Transport Security`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security

Referring to the SSLLabs `scoring guide`_ shows that our mild deficiencies comes down to key and cipher strength, neither of which are configurable with Azure Static Web Apps. What we can do is add the DNS CAA record and increase the HSTS max-age to potentially attain an A+ rank.

.. _`scoring guide`: https://github.com/ssllabs/research/wiki/SSL-Server-Rating-Guide

Moving on to our next scanning tool, we'll look at the Security `Headers scanner`_ from Probely. By entering the domain name and running the test, this tool will check what security headers our site supplies and gives a letter grade similar to the SSL test above.

.. _`Headers scanner`: https://securityheaders.com/

.. image:: images/azure-swa-security/security-headers-before.png
	:alt: Security Headers test report with grade of "C"

Our score here is a C, which isn't the best. Having security headers present and properly configured can prevent a number of nasty attacks like clickjacking and cross site scripting, along with governing browser behaviour when visiting the website. Improving our score here will be a big priority, with another A+ being the goal.

Finally, we'll take a look at the security tool provided by Hardenize_. This scanner is more general than the two previous tools, covering DNS, Email, and Web security. Like before, enter the domain name and run the test to have the report generate. The report isn't a letter grade this time, instead we have indicator boxes for each feature.

.. _Hardenize: https://www.hardenize.com/

.. image:: images/azure-swa-security/hardenize-dns-before.png
	:alt: DNS section of Hardenize test with DNS CAA and DNSSEC greyed out

Starting with the DNS section of our report, our DNS servers are in good shape and we already know the CAA record is missing. What's also missing here is DNSSEC or `DNS Security Extensions`_, which uses a public/private key pair to sign DNS records and ensure that when a request is made to the kevindreid.com domain, only signed authentic records are returned.

.. _`DNS Security Extensions`: https://www.icann.org/resources/pages/dnssec-what-is-it-why-important-2019-03-05-en

.. image:: images/azure-swa-security/hardenize-www-before.png
	:alt: Web section of Hardenize test with 3 orange warnings and 3 greyed out sections

Moving on to the web section of the Hardenize report, we see a few warnings marked in orange. Mixed content refers to insecure HTTP links being present on the website, the 1 warning being about the Pelican link in the footer of each page. The HSTS warning is about the preload parameter included without being present in the `HSTS Preload List`_, with the preload list determining if HTTPS is used from the very first connection. The last warning about XSS-Protection notes that it is a legacy header which has been superseded by the Content Security Policy and should be disabled. Items marked in grey are missing headers noted in the previous report, along with a lack of Subresource Integrity which means there's no verification for externally hosted Google fonts linked in the HTML of the site.

.. _`HSTS Preload list`: https://hstspreload.org/

With the results of these 3 reports, we've determined a fair number of improvements that can be made to enhance our sites security. The goal now is to implement these changes and attain A+ ranking for SSLLabs and Security Headers tests, along with all green items on the Hardenize report.

Improving external security
===========================

HTTP headers
------------

For modification of the HTTP Response headers, we'll need to create the file ``staticwebapp.config.json`` in the root of our static site. Open the new config file and write an empty config like so::

	{
		"globalHeaders": {
		
		}
	}

The headers we want to add will fit between the nested pair of brackets, with 1 line per header defined. We'll start with disabling X-XSS-Protection, which used the browsers XSS Auditor to prevent cross site scripting attacks. Disabling this sounds like a bad idea, but major browsers like Chrome_ and Edge_ have already removed their auditor functionalities a few years ago. We'll add this header as ``"X-XSS-Protection": "0"`` to our file.

.. _Chrome: https://chromestatus.com/feature/5021976655560704
.. _Edge: https://blogs.windows.com/windows-insider/2018/07/25/announcing-windows-10-insider-preview-build-17723-and-build-18204/

Moving on, we'll add the HSTS header as ``"Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload"``. The only change we made here was upping the max-age to 2 years for inclusion in the HSTS Preload list.

The 2 other headers present (Referrer-Policy and X-Content-Type-Options) are already configured the way I want them, but I'll define them anyways in the event Azure Static Web Apps updates what default header options are set later. `Referrer-Policy`_ shows what origin site a user came from when navigating to another page, with the ``same-origin`` meaning the header is only sent when navigating on the same website and omitted from all others. `X-Content-Type-Options`_ controls whether a sites content-type header can be inferred and possibly changed by a browser, with ``nosniff`` disabling that feature.

.. _`Referrer-Policy`: https://www.w3.org/TR/referrer-policy/
.. _`X-Content-Type-Options`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options

Moving along to adding new headers, we'll look at `Content-Security-Policy`_. CSP has a wealth of options available to configure and assists with preventing cross-site scripting and data injection attacks. There are a lot of fields that can be defined with CSP, so using a `CSP generator`_ can make this process easier. These are the fields that I used for my policy:

.. _`Content-Security-Policy`: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
.. _`CSP generator`: https://report-uri.com/home/generate

	1. ``upgrade-insecure-requests`` which informs browsers that links can be upgraded to HTTPS. This is more intended for larger sites with lots of legacy HTTP URLs present, but there's no harm in enabling it despite every link already having HTTPS.
	2. ``frame-ancestors 'self'`` which specifies which parents are valid for embedded frames and content. This setting effectively replaces the `X-Frame-Options`_ header for older browsers.
	3. ``default-src 'self'`` which defines the fallback for the various other ``-src`` settings found in the full `directive list`_. This saves us from entering every single directive in the list.
	4. ``form-action 'none'`` and ``base-uri 'self'``. These 2 are not covered by the ``default-src`` directive, and we're not using forms currently so it can be disabled.
	5. ``object-src 'none'`` mostly applies to legacy elements and is better off disabled.
	6. ``style-src 'self' fonts.googleapis.com`` and ``font-src 'self' fonts.gstatic.com``, to enable loading of our fonts from Google along with the local CSS.
	7. ``report-uri https://kevindreid.report-uri.com/r/d/csp/enforce`` for sending reports of CSP violations

.. _`X-Frame-Options`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options
.. _`directive list`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/default-src

Another lengthy header is the `Permissions Policy`_, which controls what browser features are available for our site to use. Since my blog is fairly simple, most things can be disabled. Permissions Policy also benefits from a `generator`_, and since my site is simple I opted to disable nearly every standardized feature.

.. _`Permissions Policy`: https://github.com/w3c/webappsec-permissions-policy/blob/main/permissions-policy-explainer.md
.. _`generator`: https://www.permissionspolicy.com/

Next is a trio of headers centred around `cross-origin settings`_: ``Cross-Origin-Embedder-Policy`` (COEP), ``Cross-Origin-Opener-Policy`` (COOP), and ``Cross-Origin-Resource-Policy`` (CORP). These 3 newer headers don't impact our Security Headers score, but that may change in the future. Again, since our site is fairly simple, I can lock all these down to the same-origin. 

.. _`cross-origin settings`: https://scotthelme.co.uk/coop-and-coep/

The last headers I'll add are for logging, using a header called Report-To to enable the `Reporting API`_. The cross-origin settings above use the Reporting API with the ``report-to`` field to send their reports to `Report-URI`_, a service for aggregation and analysis of various logs. The `Network Error Logging`_ or NEL header was also added to track issues with the site itself, including page load errors and feature deprecation warnings.

.. _`Reporting API`: https://developer.mozilla.org/en-US/docs/Web/API/Reporting_API
.. _`Report-URI`: https://report-uri.com/
.. _`Network Error Logging`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Network_Error_Logging

With all of our headers finally specified, our ``staticwebapp.config.json`` file looks like this::

	{
		"globalHeaders": {
		  "Content-Security-Policy": "default-src 'self'; style-src 'self' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; object-src 'none'; frame-ancestors 'self'; form-action 'none'; upgrade-insecure-requests; base-uri 'self'; report-uri https://kevindreid.report-uri.com/r/d/csp/enforce",
		  "Cross-Origin-Embedder-Policy": "require-corp; report-to='default'",
		  "Cross-Origin-Opener-Policy": "same-origin; report-to='default'",
		  "Cross-Origin-Resource-Policy": "same-origin",
		  "NEL": "{'report_to':'default','max_age':31536000,'include_subdomains':true}",
		  "Permissions-Policy": "accelerometer=(), ambient-light-sensor=(), autoplay=(), battery=(), camera=(), cross-origin-isolated=(), display-capture=(), document-domain=(), encrypted-media=(), execution-while-not-rendered=(), execution-while-out-of-viewport=(), fullscreen=(), geolocation=(), gyroscope=(), keyboard-map=(), magnetometer=(), microphone=(), midi=(), navigation-override=(), payment=(), picture-in-picture=(), publickey-credentials-get=(), screen-wake-lock=(), sync-xhr=(), usb=(), web-share=(), xr-spatial-tracking=()",
		  "Referrer-Policy": "same-origin",
		  "Report-To": "{'group':'default','max_age':31536000,'endpoints':[{'url':'https://kevindreid.report-uri.com/a/d/g'}],'include_subdomains':true}",
		  "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
		  "X-Content-Type-Options": "nosniff",
		  "X-Frame-Options": "sameorigin",
		  "X-XSS-Protection": "0"
		}
	}

On a normal SWA website using raw HTML/CSS, adding this config file would be as simple as dropping it in the root of our Github repo. Since we're using the static site generator Pelican, we have to add the line ``config_file_location: "./"`` to our YAML workflow file. This setting is only documented in the Github repo for the `static-web-apps-deploy`_ Github Action, and tells our workflow to look in the root of our repo for the config file.

.. _`static-web-apps-deploy`: https://github.com/Azure/static-web-apps-deploy/blob/v1/action.yml

DNS records
-----------

For the DNS section we'll start with the CAA record, where we must first check what Certificate Authority we get our certificate from. Referring back to this screenshot from the first article, we can see our CA is Digicert.

.. image:: images/azure-swa-website/custom-domain.png
	:alt: Static site with custom domain showing SSL cert status

To set the proper record, go to your DNS settings and add a CAA record. You can also use SSLMate's `CAA record generator`_ to build a record or list of records for your particular setup if needed. For my setup I use Cloudflare for DNS and as a registrar, so adding the record is pretty straightforward.

.. _`CAA record generator`: https://sslmate.com/caa/

.. image:: images/azure-swa-security/cf-dns-caa.png
	:alt: Cloudflare DNS entry for CAA record

Enabling DNSSEC on Cloudflare is also easy as they have an automatic DNSSEC record that generates within 24 hours. Go to DNS → Settings and click the ``Enable DNSSEC`` button at the top, easy as that!

Protecting the Backend
======================

Improving the security of our website isn't only done externally with headers and DNS records. We can also secure how our site is deployed, starting with the SWA resource itself. Azure provides `Resource Locks`_, which can protect against unwanted modifications or accidental deletion. A Resource Lock can be read-only or prevent deletion, and can be applied to a subscription, resource group, or individual resource. In this case, we'll apply a lock to the SWA resource to prevent deletion.

.. _`Resource Locks`: https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/lock-resources?tabs=json

.. image:: images/azure-swa-security/azure-resource-lock.png
	:alt: Prevent delete locak applied to SWA resource

We can also tighten security on the Github repo. There are plenty of rules and features that can be used, but since I'm the lone contributor I've only enabled a small selection of them:

	1. `Secret scanning`_ to scan code as it is pushed to the repo and block pushes that contain secret keys
	2. `Branch protection`_ to protect the production branch. The prod branch cannot be pushed to directly and will only be updated via pull request from the test branch after deployment to the SWA preview environment. `Verified commits` were also enabled.
	3. Private vulnerability reporting and security advisories for reporting of security issues within the repo
	
.. _`Secret scanning`: https://docs.github.com/en/enterprise-cloud@latest/code-security/secret-scanning/about-secret-scanning#about-secret-scanning-for-partner-patterns
.. _`Branch protection`: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
.. _`Verified commits`: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification

Results
=======

Now that our site has been hardened, let's review our scoring starting with the SSL certificate:

.. image:: images/azure-swa-security/ssl-report-after.png
	:alt: Qualys SSL server test with grade "A", DNS CAA record and long HSTS time noted

Our score here hasn't reached the A+ grade I wanted, despite the HSTS max-age increase. Looking through the `scoring guide`_ again, the cause seems to be the missing TLS_FALLBACK_SCSV feature, which governs fallback to less secure TLS versions when the client and server mismatch. This can't be controlled by us, so it's up to Microsoft to add the feature or Qualys to adjust their grading system.

Moving along to our security headers, things are greatly improved here:

.. image:: images/azure-swa-security/security-headers-after.png
	:alt: Security Headers test report with grade of "A+"

The A+ grade we were looking for is finally attained. We've added not only the required headers, but the newer cross-origin and reporting headers too.

Our last report comes from Hardenize, and we see great improvements here too:

.. image:: images/azure-swa-security/hardenize-dns-after.png
	:alt: DNS section of Hardenize test with all sections green

All sections of the DNS report are green now. While DNS CAA was verified with the Qualys report, we can also verify DNSSEC with DNSViz_, which has a nice graphical interface that shows each stage of the chain of trust for our DNS records.

.. _DNSViz: https://dnsviz.net/

.. image:: images/azure-swa-security/hardenize-www-after.png
	:alt: Web section of Hardenize test with almost all sections green

For the web part of the Hardenize report, nearly every section is green. The one mixed content warning was fixed, and our site has been added to the HSTS preload list. The other sections dealt with headers, which are now added or fixed. The only remaining grey section is Subresource Integrity with our externally-hosted Google fonts, which will be addressed in a future post.

Conclusion
==========

With that, our website security has been greatly improved. We've tackled everything from HTTP headers to DNS records, and even the Github repo and static web app resource itself. We're well prepared for anything that may attempt an attack, despite the minor limitations imposed by the platform keeping us from a perfect SSL score. Hopefully you can take away some useful ideas for your own website security. Thanks for reading!
