"use client"; // Needed for useState and useRef

/* eslint-disable react/no-unescaped-entities */

import { useState, useRef, useEffect } from 'react'; // Import useEffect
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion";
import { Play } from 'lucide-react'; // Import Play icon

export default function Home() {
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handlePlayClick = () => {
    setIsPlaying(true);
  };

  useEffect(() => {
    if (isPlaying && videoRef.current) {
      videoRef.current.play().catch(error => {
        console.error("Video play failed:", error);
        if (videoRef.current) videoRef.current.controls = true;
      });
    }
  }, [isPlaying]);

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Hero Section */}
      <section className="py-12 lg:py-8">
        <div className="mb-20">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-8 text-primary">
            Building Facebook ads doesn&apos;t need to be painful
          </h1>
          
          <div className="text-xl md:text-2xl leading-relaxed mb-12 text-foreground">
            <p>Pablo makes ad creation 10× faster and eliminates errors. No more copy-pasting into Meta Ads Manager. Pablo integrates with Notion or Airtable to automate your creative workflows.</p>
            <p className="mt-4">Now in private beta, generating 1,000+ ads per month.</p>
          </div>
      
          <Button variant="accent" size="lg" asChild>
            <a href="https://trampoline-analytics.notion.site/1aed8901aa2780fb86aacf588ebd6384">
              Join waitlist
            </a>
          </Button>
        </div>

        {/* Video Demo Section - Updated */}
        <div className="mt-20 mb-20">
          <div className="relative rounded-lg overflow-hidden shadow-xl aspect-video">
            {!isPlaying ? (
              // Placeholder Div
              <div 
                className="absolute inset-0 bg-cover bg-center cursor-pointer flex items-center justify-center group"
                style={{ backgroundImage: "url('/videos/pablo_demo_v1_thumbnail.jpg')" }}
                onClick={handlePlayClick}
              >
                {/* Subtle overlay on hover */}
                <div className="absolute inset-0 bg-black/10 group-hover:bg-black/30 transition-colors duration-200"></div>
                {/* Play Button */}
                <button 
                  aria-label="Play video"
                  className="relative z-10 rounded-full bg-white/30 p-4 text-white backdrop-blur-sm transition-all duration-200 group-hover:bg-white/50 group-hover:scale-110"
                >
                   <Play className="h-10 w-10 fill-white" />
                </button>
              </div>
            ) : (
              // Video Player
              <video
                ref={videoRef}
                className="w-full h-full object-cover"
                controls // Show controls once playing
                autoPlay   // Add autoPlay attribute
                preload="auto" // Start loading when placeholder clicked
                onEnded={() => setIsPlaying(false)} // Optional: reset to placeholder when finished
              >
                <source src="https://pub-57c5ca58566d4b0eb59f328c6e5a6361.r2.dev/pablo_demo_v1.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            )}
          </div>
        </div>
        
        {/* Features Section */}
        <div className="">
          <h2 className="text-3xl md:text-4xl font-bold mb-12 text-primary">Features</h2>
          
          <div className="grid md:grid-cols-2 gap-x-12 gap-y-8">
            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary">Naming convention compliance</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Ensure all your ads follow your naming conventions automatically.</p>
              </CardContent>
            </Card>
            
            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary">Customised assets</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Support for customized square and vertical formats (more formats coming soon).</p>
              </CardContent>
            </Card>
            
            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary">Build from where you already work</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">BYO Notion or Airtable databases or use our templates.</p>
              </CardContent>
            </Card>
            
            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary">Template inheritance</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Inherits tracking, social profile linking and Advantage+ AI preferences from a template ad.</p>
              </CardContent>
            </Card>
            
            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary">Actionable feedback</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">If Pablo has any problems, they are reported back as comments for easy troubleshooting.</p>
              </CardContent>
            </Card>
            
            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary">Instant forms creation</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Experimental support for instant forms creation.</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-20">
          <h2 className="text-3xl md:text-4xl font-bold mb-12 text-primary">Frequently Asked Questions</h2>
          
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="workflow">
              <AccordionTrigger className="text-primary">How does Pablo integrate with my existing workflow?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                Pablo connects with Notion, Airtable, and other data sources to pull your ad content. You can structure your data however you like, and Pablo will map it to the right fields in Meta Ads Manager. This means you can keep using your existing tools and workflows while automating the tedious parts.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="ads">
              <AccordionTrigger className="text-primary">What types of ads can I create with Pablo?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                Currently, Pablo supports Image and Video ad formats with square and vertical assets. We're working on adding support for Carousel ads and more asset formats in the near future. Pablo inherits tracking, social profile linking, and Advantage+ AI preferences from your template ads.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="errors">
              <AccordionTrigger className="text-primary">How does Pablo handle errors?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                Pablo validates your ad content before submission and reports any errors back as comments in your source data. This means you will know exactly what needs to be fixed and where. Common errors include missing required fields, invalid URLs, or asset dimension issues.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="limitations">
              <AccordionTrigger className="text-primary">Are there any limitations I should be aware of?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                Due to Meta's API limitations, there may be a limit to how many ads can be built in an hour. Pablo is designed to work within these constraints and will queue your requests appropriately. Additionally, some advanced Meta Ads Manager features may require manual configuration in the Meta interface.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="cost">
              <AccordionTrigger className="text-primary">How much does Pablo cost?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                Pablo is currently in beta and is $100USD per month for beta testers. We will be launching a subscription model in the future.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="access">
              <AccordionTrigger className="text-primary">How do I get access to Pablo?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                While we are in testing you will need to <a href="https://developers.facebook.com/" className="text-primary hover:underline">set up a developer account</a>, then give us your Facebook ID (you can paste your profile URL into <a href="https://lookup-id.com/#" className="text-primary hover:underline">this tool</a>). We&apos;ll then add you to the beta list and you&apos;ll need to <a href="https://developers.facebook.com/settings/developer/requests/" className="text-primary hover:underline">accept our invitation here</a>.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </section>
    </div>
  );
} 
