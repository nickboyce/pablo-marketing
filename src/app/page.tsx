"use client"; // Needed for useState and useRef

/* eslint-disable react/no-unescaped-entities */

import { useState, useRef, useEffect } from 'react'; // Import useEffect
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion";
import { Play } from 'lucide-react'; // Import Play icon
import { posthog } from '../lib/posthog';

export default function Home() {
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handlePlayClick = () => {
    setIsPlaying(true);
    posthog.capture('video_play_clicked', {
      video_type: 'demo',
      location: 'hero_section'
    });
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
            Stop wasting time uploading ads. Start scaling creative.
          </h1>
          
          <div className="text-xl md:text-2xl leading-relaxed mb-12 text-foreground">
            <p>Pablo automates Facebook ad uploads from Notion, Airtable, and Google Sheets – making creative workflows 10× faster and error-free. More creative diversity, less manual work.</p>
          </div>
      
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <Button variant="accent" size="lg" asChild>
              <a
                href="https://app.pablo.social/auth/register" target="_blank"
                onClick={() => posthog.capture('start_free_trial_clicked', { location: 'hero_section' })}
              >
                Start free trial
              </a>
            </Button>
            <p className="text-sm text-muted-foreground">
              Free for 30 days. No credit card required.
            </p>
          </div>
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
          <h2 className="text-3xl md:text-4xl font-bold mb-12 text-primary">Fits your process. Amplifies your output.</h2>
          <div className="text-xl md:text-2xl leading-relaxed mb-12 text-foreground">
            <p>Pablo plugs into your existing creative workflows so your team can keep working the way they already do, just 10× faster.</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-x-12 gap-y-8">
            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary flex items-center gap-2">
                  <a href="https://docs.pablo.social/integrations/api/" target="_blank" className="hover:underline">Pablo API</a>
                  <span className="text-xs font-medium bg-green-100 text-green-800 px-1.5 py-0 rounded-full">NEW</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Meta API cheat code. Single API endpoint to create ads from your agents or automations.</p>
              </CardContent>
            </Card>

            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary flex items-center gap-2">
                  <a href="https://docs.pablo.social/integrations/mcp/" target="_blank" className="hover:underline">Pablo MCP</a>
                  <span className="text-xs font-medium bg-green-100 text-green-800 px-1.5 py-0 rounded-full">NEW</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Plug Pablo into Claude, Cursor or any MCP-compatible agent.</p>
              </CardContent>
            </Card>

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
                <CardTitle className="text-primary">
                  <a href="https://docs.pablo.social/guides/placement-assets/" target="_blank" className="hover:underline">Placement-specific assets</a>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Square, 4:5 and 9:16 in any combination, mapped to the right placements automatically.</p>
              </CardContent>
            </Card>

            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary">Build from where you already work</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">BYO Notion, Airtable or Google Sheets or use our templates.</p>
              </CardContent>
            </Card>

            <Card className="bg-card">
              <CardHeader>
                <CardTitle className="text-primary flex items-center gap-2">
                  <a href="https://docs.pablo.social/guides/partnership-ads/" target="_blank" className="hover:underline">Partnership ads</a>
                  <span className="text-xs font-medium bg-green-100 text-green-800 px-1.5 py-0 rounded-full">BETA</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground">Run collaborative ads with creator and brand partners.</p>
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
                Pablo supports Image, Video and Carousel ads with square, vertical and 4:5 assets in any combination. Pablo inherits tracking, social profile linking, and Advantage+ AI preferences from your template ads.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="errors">
              <AccordionTrigger className="text-primary">How does Pablo handle errors?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                Pablo validates your ad content before submission and reports any errors back as comments in your source data. This means you will know exactly what needs to be fixed and where. Common errors include missing required fields, invalid URLs, or asset dimension issues.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="cost">
              <AccordionTrigger className="text-primary">How much does Pablo cost?</AccordionTrigger>
              <AccordionContent className="text-foreground">
                Pablo is $99USD per month.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </section>
    </div>
  );
} 
