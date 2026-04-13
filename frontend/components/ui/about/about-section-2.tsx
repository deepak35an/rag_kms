"use client";
import { TimelineContent } from "@/components/ui/about/timeline-animation";
import { Zap } from "lucide-react";
import { useRef } from "react";

export default function AboutSection2() {
  const heroRef = useRef<HTMLDivElement>(null);
  const revealVariants = {
    visible: (i: number) => ({
      y: 0,
      opacity: 1,
      filter: "blur(0px)",
      transition: {
        delay: i * 1.5,
        duration: 0.7,
      },
    }),
    hidden: {
      filter: "blur(10px)",
      y: 40,
      opacity: 0,
    },
  };
  const textVariants = {
    visible: (i: number) => ({
      filter: "blur(0px)",
      opacity: 1,
      transition: {
        delay: i * 0.3,
        duration: 0.7,
      },
    }),
    hidden: {
      filter: "blur(10px)",
      opacity: 0,
    },
  };
  return (
    <section className="py-32 px-4 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto" ref={heroRef}>
        <div className="flex flex-col lg:flex-row items-start gap-8">
          {/* Right side - Content */}
          <div className="flex-1">
            <TimelineContent
              as="h1"
              animationNum={0}
              timelineRef={heroRef}
              customVariants={revealVariants}
              className="sm:text-4xl text-2xl md:text-5xl leading-[110%]! font-semibold text-gray-900 mb-8"
            >
              We are{" "}
              <TimelineContent
                as="span"
                animationNum={1}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="text-blue-600 border-2 border-blue-500 inline-block xl:h-16  border-dotted px-2 rounded-md"
              >
                rethinking
              </TimelineContent>{" "}
              vehicle charging to be more reliable and always you-first. Our
              goal is to continually raise the bar and{" "}
              <TimelineContent
                as="span"
                animationNum={2}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="text-orange-600 border-2 border-orange-500 inline-block xl:h-16 border-dotted px-2 rounded-md"
              >
                challenge
              </TimelineContent>{" "}
              how things could{" "}
              <TimelineContent
                as="span"
                animationNum={3}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="text-green-600 border-2 border-green-500 inline-block xl:h-16 border-dotted px-2 rounded-md"
              >
                work for you.
              </TimelineContent>
            </TimelineContent>

            <div className="mt-12 flex gap-2 justify-between">
              <TimelineContent
                as="div"
                animationNum={4}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="mb-4 sm:text-xl text-xs"
              >
                <div className=" font-medium text-gray-900 mb-1 capitalize">
                  We are Electra and we will
                </div>
                <div className=" text-gray-600 font-semibold uppercase">
                  take you further
                </div>
              </TimelineContent>

              <TimelineContent
                as="button"
                animationNum={5}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="bg-blue-600 gap-2 font-medium shadow-lg shadow-blue-600 text-white h-12 px-4 rounded-full text-sm inline-flex items-center cursor-pointer"
              >
                <Zap fill="white" size={16} />
                About Electra
              </TimelineContent>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}