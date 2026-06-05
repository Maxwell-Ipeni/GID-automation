import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy - GlowNest Finds',
  description: 'Privacy Policy for GlowNest Finds Amazon Affiliate Pinterest Automation',
};

export default function PrivacyPolicy() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Privacy Policy</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-8">
        <p className="text-sm text-gray-500">Last updated: June 2026</p>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Who We Are</h2>
          <p className="text-gray-700 leading-relaxed">
            GlowNest Finds ("we," "us," or "our") operates the website and platform located at our application.
            We are an Amazon affiliate Pinterest automation platform that helps users discover trending Amazon products,
            generate affiliate links, and publish Pinterest pins automatically.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">2. What Data We Collect</h2>
          <p className="text-gray-700 leading-relaxed mb-3">
            We collect the following types of data to operate our service:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700">
            <li>
              <strong>Publicly Available Amazon Product Data:</strong> We scrape publicly accessible Amazon product
              information including product names, prices, images, ASINs, ratings, and bestseller rankings from
              Amazon&apos;s Best Sellers, Movers & Shakers, New Releases, and Deals pages. This data is publicly
              available on Amazon&apos;s website.
            </li>
            <li>
              <strong>Amazon Affiliate Tags:</strong> We store your Amazon Associates tracking tag (e.g., "yourtag-20")
              which you voluntarily provide. This is used exclusively to generate affiliate-compliant product links.
            </li>
            <li>
              <strong>Pinterest API Credentials:</strong> We store your Pinterest access token and board ID, which
              you voluntarily provide through our Settings page. These are used exclusively to publish pins to your
              designated Pinterest board via the official Pinterest API.
            </li>
            <li>
              <strong>Pinterest Post Data:</strong> We store data related to your scheduled and published Pinterest
              pins, including pin titles, descriptions, images, affiliate links, and publishing timestamps.
            </li>
            <li>
              <strong>Scraping Logs:</strong> We maintain logs of scraping operations including the source accessed,
              number of products found, timestamps, and any errors encountered.
            </li>
            <li>
              <strong>Usage Information:</strong> We may collect basic usage metrics including which pages are
              accessed, API requests made, and system performance data to improve our service.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">3. How We Use Your Data</h2>
          <p className="text-gray-700 leading-relaxed">
            We use the collected data solely for the following purposes:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>Discovering and storing publicly available Amazon product listings</li>
            <li>Generating Amazon affiliate links with your designated tracking tag</li>
            <li>Creating and publishing Pinterest pins to your account via the Pinterest API</li>
            <li>Managing a publishing queue with scheduled and random delays to prevent spam-like behavior</li>
            <li>Generating and processing Pinterest-optimized images for published pins</li>
            <li>Providing our dashboard interface with product feeds, trending data, and publishing status</li>
            <li>Monitoring system health, scraping job status, and publishing queue health</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Data Sharing and Disclosure</h2>
          <p className="text-gray-700 leading-relaxed">
            We do not sell, trade, or rent your personal data to third parties. Data sharing is limited to the
            following circumstances:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>
              <strong>Amazon:</strong> When you click an affiliate link, you are directed to Amazon&apos;s website.
              Amazon&apos;s privacy policy governs their data collection. We have no control over Amazon&apos;s data practices.
            </li>
            <li>
              <strong>Pinterest:</strong> When pins are published, the associated data (title, description, image,
              affiliate link) is shared with Pinterest via their official API. Pinterest&apos;s privacy policy governs
              their data collection.
            </li>
            <li>
              <strong>Service Providers:</strong> We may use third-party services for hosting, database, and
              infrastructure (such as Convex DB, Docker, and Vercel/hosting providers). These providers are
              contractually obligated to handle your data securely and only for the purposes we specify.
            </li>
            <li>
              <strong>Legal Requirements:</strong> We may disclose data if required by law, court order, or
              governmental regulation, or if we believe disclosure is necessary to protect our rights or the
              safety of others.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Amazon and Pinterest Integrations</h2>
          <p className="text-gray-700 leading-relaxed">
            Our platform integrates with Amazon&apos;s public product pages and Pinterest&apos;s official API.
            These integrations operate under the following conditions:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>
              We do not have a direct partnership with Amazon or Pinterest. Our use of their services is
              subject to their respective terms of service and privacy policies.
            </li>
            <li>
              We comply with Amazon&apos;s Associates Program Operating Agreement, including requirements around
              linking and disclosures.
            </li>
            <li>
              We comply with Pinterest&apos;s API terms of service and community guidelines for automated posting.
            </li>
            <li>
              We use randomized publishing delays and queue management to ensure our posting behavior does not
              resemble spam or automated abuse.
            </li>
            <li>
              Any affiliate commissions earned through our generated links are governed solely by Amazon&apos;s
              Associates Program terms — we have no control over, and do not receive, those commissions directly.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Data Retention</h2>
          <p className="text-gray-700 leading-relaxed">
            We retain your data for as long as your account is active or as needed to provide our services:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>
              <strong>Affiliate credentials and settings:</strong> Retained until you delete your account or
              request removal of your data.
            </li>
            <li>
              <strong>Pinterest credentials:</strong> Retained until you revoke access through Pinterest&apos;s
              settings, delete your account, or request data removal.
            </li>
            <li>
              <strong>Scraped product data:</strong> Publicly available Amazon product data is retained as
              part of our product database and may be refreshed or updated during subsequent scraping operations.
            </li>
            <li>
              <strong>Publishing logs:</strong> Retained for up to 90 days for debugging and quality purposes.
            </li>
            <li>
              <strong>Pinterest posts:</strong> Retained as part of your publishing history for as long as
              your account is active.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Cookies and Tracking</h2>
          <p className="text-gray-700 leading-relaxed">
            We use minimal cookies and tracking:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>
              <strong>Essential cookies:</strong> We may use session cookies to maintain your logged-in state
              and preferences within our dashboard. These are necessary for the service to function.
            </li>
            <li>
              <strong>No third-party advertising cookies:</strong> We do not use advertising or tracking
              cookies from third-party networks.
            </li>
            <li>
              <strong>Convex DB cookies:</strong> If you use Convex authentication, Convex&apos;s own cookie
              policy applies to that authentication flow.
            </li>
            <li>
              <strong>Pinterest:</strong> Pinterest may set cookies when you authorize our application to
              access your Pinterest account. Refer to Pinterest&apos;s cookie policy for details.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Data Security</h2>
          <p className="text-gray-700 leading-relaxed">
            We take data security seriously and implement the following measures:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>All API communications are transmitted over HTTPS (TLS/SSL encryption)</li>
            <li>Credentials (Amazon tags, Pinterest tokens) are stored in environment variables or secure config, not in plain code</li>
            <li>Access to our infrastructure is restricted and monitored</li>
            <li>We use reputable third-party services (Convex, Docker, hosting providers) that maintain industry-standard security certifications</li>
            <li>
              Our scraping operations include rate limiting and randomized delays to prevent excessive load
              on Amazon&apos;s servers and to avoid triggering anti-bot protections
            </li>
          </ul>
          <p className="text-gray-700 leading-relaxed mt-2">
            No method of transmission over the internet is 100% secure. While we strive to protect your data,
            we cannot guarantee absolute security. You are responsible for keeping your API credentials
            confidential and for revoking access when it is no longer needed.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">9. Your Rights</h2>
          <p className="text-gray-700 leading-relaxed">
            Depending on your location, you may have the following rights regarding your personal data:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>
              <strong>Access:</strong> You may request a copy of the personal data we hold about you.
            </li>
            <li>
              <strong>Deletion:</strong> You may request the deletion of your account data at any time by
              contacting us or using the account deletion option in Settings.
            </li>
            <li>
              <strong>Correction:</strong> You may update or correct your stored credentials through the
              Settings page.
            </li>
            <li>
              <strong>Withdrawal of consent:</strong> If our processing is based on your consent, you may
              withdraw it at any time by deleting your account or removing your credentials.
            </li>
            <li>
              <strong>Objection:</strong> You may object to certain types of processing of your data.
            </li>
            <li>
              <strong>Data portability:</strong> Where applicable, you may request your data in a
              machine-readable format.
            </li>
          </ul>
          <p className="text-gray-700 leading-relaxed mt-2">
            To exercise any of these rights, contact us through the contact information provided below.
            We will respond to valid requests within 30 days.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">10. Children&apos;s Privacy</h2>
          <p className="text-gray-700 leading-relaxed">
            Our service is not intended for individuals under the age of 18. We do not knowingly collect
            personal data from minors. If we become aware that a minor has provided us with personal data,
            we will take steps to delete such data promptly.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">11. International Data Transfers</h2>
          <p className="text-gray-700 leading-relaxed">
            Our platform may involve data transfer across international borders. If you are located
            outside the country where our servers are hosted, your data may be transferred internationally.
            We ensure that such transfers are conducted in accordance with applicable data protection laws
            and that appropriate safeguards are in place.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">12. Third-Party Links</h2>
          <p className="text-gray-700 leading-relaxed">
            Our platform may contain links to third-party websites, including Amazon and Pinterest. These
            websites have their own privacy policies governing their data collection and use. We are not
            responsible for the practices of these third-party sites. We encourage you to review the
            privacy policies of Amazon, Pinterest, and any other third-party sites you visit.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">13. Scraping Disclaimer</h2>
          <p className="text-gray-700 leading-relaxed">
            Our platform scrapes publicly accessible pages on Amazon to collect product information
            including bestseller rankings, prices, ratings, and product details. This data is publicly
            available on Amazon&apos;s website and is collected solely for the purpose of providing affiliate
            marketing automation. We:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>Respect Amazon&apos;s robots.txt directives where applicable</li>
            <li>Use rate limiting and randomized delays to minimize server load</li>
            <li>Only collect publicly available, non-authenticated data</li>
            <li>Do not bypass paywalls, CAPTCHAs, or other access controls</li>
            <li>Operate on the assumption that publicly accessible product data may be collected for affiliate purposes</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">14. Changes to This Policy</h2>
          <p className="text-gray-700 leading-relaxed">
            We may update this Privacy Policy from time to time to reflect changes in our practices,
            technology, or legal requirements. When we make material changes, we will:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 mt-2">
            <li>Update the "Last updated" date at the top of this page</li>
            <li>Post the revised policy on our platform</li>
            <li>Notify you through the dashboard or registered email where appropriate</li>
          </ul>
          <p className="text-gray-700 leading-relaxed mt-2">
            We encourage you to review this Privacy Policy periodically for any changes.
            Continued use of the service after changes constitutes acceptance of the updated policy.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">15. Contact Us</h2>
          <p className="text-gray-700 leading-relaxed">
            If you have any questions, concerns, or requests regarding this Privacy Policy or our
            data practices, please contact us at:
          </p>
          <div className="mt-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-gray-700"><strong>GlowNest Finds</strong></p>
            <p className="text-gray-600 text-sm mt-1">
              For privacy-related inquiries, please include "Privacy Policy" in your subject line.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}